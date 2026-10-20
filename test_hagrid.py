"""Image preprocessing, model failures and offline inference smoke tests."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

import hagrid_classifier as hagrid
from test_gestures import compact_thumb, pair


def logits(*labels):
    rows = np.zeros((len(labels), 45), np.float32)
    for row, label in zip(rows, labels):
        if label is not None:
            row[label] = 12
    return rows


class FakeNet:
    def __init__(self, output):
        self.output = output
        self.blob = None
        self.calls = 0

    def setInput(self, blob):
        self.blob = blob

    def forward(self):
        self.calls += 1
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


class HagridTests(unittest.TestCase):
    def setUp(self):
        self.rgb = np.full((360, 640, 3), [255, 0, 0], dtype=np.uint8)

    def test_rgb_channels_normalization_and_two_hand_batch(self):
        net = FakeNet(logits(27, 24))
        classifier = hagrid.HagridClassifier(net=net)
        self.assertEqual(classifier.predict(self.rgb, pair(compact_thumb())), ['up', 'down'])
        self.assertEqual(net.calls, 1)
        self.assertEqual(net.blob.shape, (2, 3, 128, 128))
        self.assertEqual(net.blob.dtype, np.float32)
        self.assertTrue(net.blob.flags.c_contiguous)
        np.testing.assert_allclose(net.blob[:, 0], 1)
        np.testing.assert_allclose(net.blob[:, 1:], -127 / 128)

    def test_confident_non_thumb_vetoes_and_uncertainty_defers(self):
        net = FakeNet(logits(25, None))
        classifier = hagrid.HagridClassifier(net=net)
        self.assertEqual(classifier.predict(self.rgb, pair(compact_thumb())), ['other', None])

    def test_rotated_down_label_maps_to_thumbs_down(self):
        classifier = hagrid.HagridClassifier(net=FakeNet(logits(6)))
        self.assertEqual(classifier.predict(self.rgb, [compact_thumb()]), ['down'])

    def test_invalid_first_crop_preserves_second_hand_alignment(self):
        net = FakeNet(logits(27))
        classifier = hagrid.HagridClassifier(net=net)
        self.assertEqual(classifier.predict(self.rgb, [[], compact_thumb()]), [None, 'up'])
        self.assertEqual(net.blob.shape[0], 1)

    def test_empty_tiny_or_nonfinite_hands_do_not_run_inference(self):
        net = FakeNet(logits(27))
        classifier = hagrid.HagridClassifier(net=net)
        invalid = compact_thumb()
        invalid[4][0] = np.nan
        self.assertEqual(classifier.predict(self.rgb, []), [])
        self.assertEqual(classifier.predict(self.rgb, [[], [[.5, .5]] * 21, invalid]), [None] * 3)
        self.assertEqual(net.calls, 0)
        self.assertTrue(classifier.enabled)

    def test_edge_crop_is_bounded_and_contains_image_pixels(self):
        hand = [[x - .3, y] for x, y in compact_thumb()]
        crop = hagrid.hand_crop(self.rgb, hand)
        self.assertIsNotNone(crop)
        self.assertTrue(np.shares_memory(crop, self.rgb))
        self.assertGreaterEqual(crop.shape[0], 12)
        self.assertGreaterEqual(crop.shape[1], 12)
        self.assertLessEqual(crop.shape[0], self.rgb.shape[0])
        self.assertLessEqual(crop.shape[1], self.rgb.shape[1])
        self.assertIsNone(hagrid.hand_crop(self.rgb, [[x + 2, y] for x, y in hand]))

    def test_invalid_image_falls_back_without_disabling_model(self):
        net = FakeNet(logits(27))
        classifier = hagrid.HagridClassifier(net=net)
        for image in (self.rgb[:, :, 0], self.rgb.astype(np.float32)):
            self.assertIsNone(classifier.predict(image, [compact_thumb()]))
        self.assertTrue(classifier.enabled)
        self.assertEqual(net.calls, 0)

    def test_bad_outputs_or_inference_error_disable_once_and_fall_back(self):
        for output in (np.zeros((1, 44)), np.zeros((2, 45)),
                       np.full((1, 45), np.nan), np.full((1, 45), np.inf),
                       cv2.error('inference failed')):
            with self.subTest(output=type(output).__name__):
                net = FakeNet(output)
                classifier = hagrid.HagridClassifier(net=net)
                with self.assertLogs('teams-effects', level='WARNING') as logs:
                    self.assertIsNone(classifier.predict(self.rgb, [compact_thumb()]))
                    self.assertIsNone(classifier.predict(self.rgb, [compact_thumb()]))
                self.assertEqual(len(logs.records), 1)
                self.assertFalse(classifier.enabled)
                self.assertEqual(net.calls, 1)

    def test_checksum_is_checked_before_loading_the_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.onnx'
            path.write_bytes(b'not the pinned model')
            with patch.object(hagrid.cv2.dnn, 'readNetFromONNX') as load:
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    hagrid.HagridClassifier(model_path=path)
                load.assert_not_called()

    def test_invalid_manifest_is_rejected_without_loading_a_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            for spec in (None, {}, {'labels': [None] * 45}, {'labels': ['like'] * 45}):
                path.write_text(json.dumps(spec))
                with patch.object(hagrid, 'MANIFEST_PATH', path):
                    with self.assertRaisesRegex(ValueError, 'label map'):
                        hagrid.HagridClassifier(net=FakeNet(logits(27)))

    def test_missing_or_invalid_model_keeps_geometric_recognition_available(self):
        for error in (FileNotFoundError('missing model'), ValueError('bad checksum'), cv2.error('bad model')):
            with patch.object(hagrid, 'HagridClassifier', side_effect=error):
                with self.assertLogs('teams-effects', level='WARNING'):
                    self.assertIsNone(hagrid.load_classifier())

    @unittest.skipUnless(hagrid.MODEL_PATH.exists(), 'Run tools/prepare_assets.py --models-only for the model smoke test')
    def test_pinned_model_runs_on_cpu_and_does_not_find_thumbs_in_a_blank_image(self):
        classifier = hagrid.HagridClassifier()
        image = np.full_like(self.rgb, 127)
        result = classifier.predict(image, pair(compact_thumb()))
        self.assertEqual(len(result), 2)
        self.assertTrue(all(value in (None, 'other') for value in result))
        self.assertTrue(classifier.enabled)


if __name__ == '__main__':
    unittest.main()
