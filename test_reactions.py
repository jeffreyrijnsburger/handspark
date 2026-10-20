import unittest

import numpy as np

from render_reactions import DURATION, Renderer


class RainTests(unittest.TestCase):
    def test_cloud_has_transparent_padding_on_every_side(self):
        alpha = np.asarray(Renderer('rain').cloud)[:, :, 3]
        for edge in (alpha[:3], alpha[-3:], alpha[:, :3], alpha[:, -3:]):
            self.assertFalse(edge.any(), 'the cloud and its shadow must fit inside the sprite')
        self.assertGreater(int((alpha > 150).sum()), 50000)

    def test_cloud_stays_inside_video_throughout_animation(self):
        renderer = Renderer('rain')
        for t in (0.3, 1, 2.5, 4.3):
            with self.subTest(time=t):
                alpha = np.asarray(renderer.frame(t))[:, :, 3]
                # The full-frame atmospheric tint is intentional. No cloud
                # pixels may reach the top or either side of the video.
                self.assertLessEqual(int(alpha[:10].max()), 28)
                self.assertLessEqual(int(alpha[:, :100].max()), 28)
                self.assertLessEqual(int(alpha[:, -100:].max()), 28)
                self.assertGreater(int(alpha[30:185, 180:780].max()), 200)

    def test_rain_moves_and_fades_without_opaque_background(self):
        renderer = Renderer('rain')
        first = np.asarray(renderer.frame(1))
        later = np.asarray(renderer.frame(1.15))
        self.assertGreater(int(np.count_nonzero(first[240:] != later[240:])), 3000)
        self.assertLess(int(first[:, :, 3].max()), 255)
        self.assertTrue(np.array_equal(first, np.asarray(Renderer('rain').frame(1))))
        for t in (0, DURATION):
            self.assertIsNone(renderer.frame(t).getchannel('A').getbbox())


if __name__ == '__main__':
    unittest.main()
