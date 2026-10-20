import base64
import unittest
from unittest.mock import Mock

from preview_stream import frames


class PreviewStreamTests(unittest.TestCase):
    def source(self, height=720):
        obs = Mock()
        jpeg = b'\xff\xd8jpeg-frame\xff\xd9'
        def call(kind, **values):
            if kind == 'GetVideoSettings':
                return {'outputHeight': height}
            if kind == 'GetSourceScreenshot':
                return {'imageData': 'data:image/jpeg;base64,' + base64.b64encode(jpeg).decode()}
            raise AssertionError(f'Preview must never change camera settings: {kind}')
        obs.call.side_effect = call
        return obs, jpeg

    def test_composed_frames_are_capped_to_actual_output_and_rate_limited(self):
        obs, jpeg = self.source(height=360)
        clock = Mock(side_effect=[0, 0.01, 0.04])
        sleep = Mock()
        stream = frames(obs, 720, 30, clock=clock, sleep=sleep)
        self.assertEqual(next(stream), jpeg)
        self.assertEqual(next(stream), jpeg)
        stream.close()
        self.assertAlmostEqual(sleep.call_args.args[0], 1 / 30 - 0.01)
        screenshot = obs.call.call_args_list[-1]
        self.assertEqual(screenshot.kwargs['imageWidth'], 640)
        self.assertEqual(screenshot.kwargs['imageHeight'], 360)

    def test_preview_can_be_smaller_than_camera_without_changing_it(self):
        obs, jpeg = self.source(height=720)
        stream = frames(obs, 540, 24)
        self.assertEqual(next(stream), jpeg)
        stream.close()
        self.assertEqual(obs.call.call_args.kwargs['imageHeight'], 540)
        self.assertEqual(len(obs.call.call_args_list), 2)

    def test_invalid_options_are_rejected_before_contacting_obs(self):
        for resolution, fps in ((1080, 30), (360, 60), (True, 30)):
            obs, _ = self.source()
            with self.assertRaises(ValueError):
                next(frames(obs, resolution, fps))
            obs.call.assert_not_called()
