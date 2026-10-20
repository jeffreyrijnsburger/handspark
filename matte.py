"""Soft person masking for the foreground layer, only during background effects."""
from pathlib import Path
import os

import cv2
import numpy as np
from PIL import Image

from control import RUNTIME

FOREGROUND = 'Teams Foreground'
FILTER = 'Persoonsmasker'
BACKGROUND_REACTIONS = frozenset(('lasers', 'fireworks', 'balloons', 'confetti'))


def soften_person(probability, hands=(), previous=None):
    """Preserve soft hair edges and tracked fingers without large hand halos."""
    alpha = np.clip((probability - 0.20) / 0.55, 0, 1).astype(np.float32)
    h, w = alpha.shape
    for hand in hands:
        points = np.array([(round(x * w), round(y * h)) for x, y in hand], dtype=np.int32)
        if points.shape != (21, 2):
            continue
        width = max(2, round(np.linalg.norm(points[5] - points[17]) * 0.19))
        cv2.fillConvexPoly(alpha, cv2.convexHull(points[[0, 1, 2, 5, 9, 13, 17]]), 1.0)
        for chain in ([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12],
                      [13, 14, 15, 16], [17, 18, 19, 20]):
            cv2.polylines(alpha, [points[chain]], False, 1.0, width, cv2.LINE_AA)
            cv2.circle(alpha, tuple(points[chain[-1]]), max(1, width // 2), 1.0, -1)
    alpha = cv2.GaussianBlur(cv2.dilate(alpha, np.ones((3, 3), np.uint8)), (0, 0), 0.65)
    if previous is not None and previous.shape == alpha.shape:
        # Smooth stationary edges; avoid trailing silhouettes during movement.
        weight = np.where(np.abs(alpha - previous) < 0.10, 0.22, 0.0)
        alpha = alpha * (1 - weight) + previous * weight
    return np.clip(alpha, 0, 1).astype(np.float32)


class PersonMatte:
    def __init__(self, obs, camera, scene):
        import mediapipe as mp
        self.mp = mp
        self.obs = obs
        self.scene = scene
        self.previous = None
        self.slot = 0
        self.enabled = False
        self.generation = 0
        options = mp.tasks.vision.ImageSegmenterOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(
                Path(__file__).with_name('selfie_segmenter_landscape.tflite'))),
            output_confidence_masks=True)
        self.model = mp.tasks.vision.ImageSegmenter.create_from_options(options)
        RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.paths = [RUNTIME / 'person-a.png', RUNTIME / 'person-b.png']
        for path in self.paths:
            Image.new('RGBA', (320, 180), (255, 255, 255, 0)).save(path)
        scenes = obs.call('GetSceneList')['scenes']
        if not any(s['sceneName'] == FOREGROUND for s in scenes):
            obs.call('CreateScene', sceneName=FOREGROUND)
        items = obs.call('GetSceneItemList', sceneName=FOREGROUND)['sceneItems']
        if not any(x['sourceName'] == camera for x in items):
            obs.call('CreateSceneItem', sceneName=FOREGROUND, sourceName=camera, sceneItemEnabled=True)
        filters = obs.call('GetSourceFilterList', sourceName=FOREGROUND)['filters']
        settings = {'image_path': str(self.paths[0]), 'type': 'mask_alpha_filter.effect',
                    'opacity': 100, 'stretch': True}
        if not any(f['filterName'] == FILTER for f in filters):
            obs.call('CreateSourceFilter', sourceName=FOREGROUND, filterName=FILTER,
                     filterKind='mask_filter', filterSettings=settings)
        else:
            obs.call('SetSourceFilterSettings', sourceName=FOREGROUND, filterName=FILTER,
                     filterSettings=settings)
        items = obs.call('GetSceneItemList', sceneName=scene)['sceneItems']
        existing = next((x for x in items if x['sourceName'] == FOREGROUND), None)
        self.item = existing['sceneItemId'] if existing else obs.call(
            'CreateSceneItem', sceneName=scene, sourceName=FOREGROUND, sceneItemEnabled=False)['sceneItemId']
        count = len(obs.call('GetSceneItemList', sceneName=scene)['sceneItems'])
        obs.call('SetSceneItemIndex', sceneName=scene, sceneItemId=self.item, sceneItemIndex=count - 1)
        self.show(False)

    def show(self, enabled):
        self.obs.call('SetSceneItemEnabled', sceneName=self.scene, sceneItemId=self.item,
                      sceneItemEnabled=enabled)
        self.enabled = enabled
        if not enabled:
            self.previous = None

    def update(self, rgb, hands):
        image = cv2.resize(rgb, (320, 180), interpolation=cv2.INTER_AREA)
        result = self.model.segment(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=image))
        index = 0 if len(result.confidence_masks) == 1 else 1
        probability = result.confidence_masks[index].numpy_view().squeeze()
        alpha = soften_person(probability, hands, self.previous)
        self.previous = alpha
        rgba = np.full((*alpha.shape, 4), 255, dtype=np.uint8)
        rgba[:, :, 3] = (alpha * 255).astype(np.uint8)
        path = self.paths[self.slot]
        self.slot = 1 - self.slot
        temporary = path.with_suffix('.tmp.png')
        Image.fromarray(rgba).save(temporary, compress_level=1)
        os.replace(temporary, path)
        self.obs.call('SetSourceFilterSettings', sourceName=FOREGROUND, filterName=FILTER,
                      filterSettings={'image_path': str(path)})
        self.generation += 1

    def close(self):
        self.show(False)
        self.model.close()
