"""Local HaGRID image evidence for thumbs, using the existing OpenCV runtime.

Model source and license: hagrid-model.json and THIRD_PARTY_NOTICES.md.
Images and predictions are transient; inference performs no network requests.
"""
import hashlib
import json
import logging
from pathlib import Path

import cv2
import numpy as np


BASE = Path(__file__).resolve().parent
MODEL_PATH = BASE / 'hagrid_crops.onnx'
MANIFEST_PATH = BASE / 'hagrid-model.json'
LOG = logging.getLogger('teams-effects')
THUMB_LABELS = {'like': 'up', 'dislike': 'down', 'thumb_down': 'down'}


def hand_crop(rgb, landmarks):
    """Square crop with context around the normalized MediaPipe hand points."""
    if len(landmarks) != 21 or any(len(point) < 2 for point in landmarks):
        return None
    points = np.asarray([point[:2] for point in landmarks], dtype=np.float32)
    if not np.isfinite(points).all():
        return None
    height, width = rgb.shape[:2]
    points *= (width, height)
    low, high = points.min(axis=0), points.max(axis=0)
    center = (low + high) / 2
    side = float(max(high - low)) * 1.2
    if side < 12:
        return None
    left, top = np.floor(center - side / 2).astype(int)
    right, bottom = np.ceil(center + side / 2).astype(int)
    left, top = max(0, left), max(0, top)
    right, bottom = min(width, right), min(height, bottom)
    if right - left < 12 or bottom - top < 12:
        return None
    return rgb[top:bottom, left:right]


class HagridClassifier:
    def __init__(self, model_path=MODEL_PATH, *, net=None):
        spec = json.loads(MANIFEST_PATH.read_text())
        labels = spec.get('labels') if isinstance(spec, dict) else None
        if (not isinstance(labels, list) or len(labels) != 45
                or any(not isinstance(label, str) for label in labels)
                or len(set(labels)) != 45 or not THUMB_LABELS.keys() <= set(labels)):
            raise ValueError('Invalid HaGRID label map')
        self.labels = tuple(labels)
        if net is None:
            data = Path(model_path).read_bytes()
            if hashlib.sha256(data).hexdigest() != spec.get('sha256'):
                raise ValueError('HaGRID model checksum mismatch')
            net = cv2.dnn.readNetFromONNX(str(model_path))
            # Keep this small classifier from occupying all CPU threads while
            # OBS, MediaPipe and the independent preview are also running.
            cv2.setNumThreads(1)
        self.net = net
        self.enabled = True

    def predict(self, rgb, hands):
        """Return up/down, other (veto), or None (defer to geometry) per hand.

        An unavailable classifier returns None for the entire result. A high
        model score is a selection threshold, not a calibrated probability.
        """
        if not self.enabled:
            return None
        if not hands:
            return []
        if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
            return None
        predictions = [None] * len(hands)
        crops, indices = [], []
        try:
            for index, hand in enumerate(hands):
                crop = hand_crop(rgb, hand)
                if crop is not None:
                    crops.append(cv2.resize(crop, (128, 128), interpolation=cv2.INTER_LINEAR))
                    indices.append(index)
            if not crops:
                return predictions
            # Controller frames are already RGB. Match the upstream model's
            # normalization without swapping red and blue a second time.
            blob = (np.stack(crops).astype(np.float32) - 127.0) / 128.0
            self.net.setInput(np.ascontiguousarray(blob.transpose(0, 3, 1, 2)))
            logits = np.asarray(self.net.forward(), dtype=np.float32)
            if logits.shape != (len(crops), len(self.labels)) or not np.isfinite(logits).all():
                raise ValueError('Invalid HaGRID model output')
            scores = np.exp(logits - logits.max(axis=1, keepdims=True))
            scores /= scores.sum(axis=1, keepdims=True)
            for index, row in zip(indices, scores):
                first = int(np.argmax(row))
                if row[first] >= 0.8:
                    predictions[index] = THUMB_LABELS.get(self.labels[first], 'other')
        except (cv2.error, ValueError, RuntimeError) as error:
            self.enabled = False
            LOG.warning('HaGRID inference disabled; using geometric recognition: %s', error)
            return None
        return predictions


def load_classifier():
    try:
        return HagridClassifier()
    except (OSError, ValueError, cv2.error) as error:
        LOG.warning('HaGRID unavailable; using geometric recognition: %s', error)
        return None
