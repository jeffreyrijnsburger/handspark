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

    def test_lightning_has_two_localized_strikes_and_lights_the_cloud(self):
        renderer = Renderer('rain')
        bolts = renderer.bolts
        for t in (1.38, 3.43):
            with self.subTest(time=t):
                lit = np.asarray(renderer.frame(t)).astype(float)
                renderer.bolts = ()
                plain = np.asarray(renderer.frame(t)).astype(float)
                renderer.bolts = bolts
                self.assertGreater(int((lit[200:430, :, 0] > 225).sum()), 300)
                self.assertGreater(float((lit - plain)[70:160, 240:700, :3].mean()), 10)
                self.assertTrue(np.array_equal(lit[:, :100], plain[:, :100]))
                self.assertTrue(np.array_equal(lit[:, -100:], plain[:, -100:]))
        for t in (0.5, 2, 4):
            lit = np.asarray(renderer.frame(t))
            renderer.bolts = ()
            self.assertTrue(np.array_equal(lit, np.asarray(renderer.frame(t))))
            renderer.bolts = bolts


class ThumbVisualTests(unittest.TestCase):
    def test_golden_thumb_keeps_its_color_and_animation_at_meeting_resolution(self):
        renderer = Renderer('thumbs_up')
        first = np.asarray(renderer.frame(0.35).resize((640, 360)))
        later = np.asarray(renderer.frame(1.8).resize((640, 360)))
        gold = (later[:, :, 0] > 220) & (later[:, :, 1] > 120) & (later[:, :, 1] < 235) & (later[:, :, 2] < 100)
        self.assertGreater(int(gold.sum()), 1200)
        self.assertGreater(float(np.mean(np.abs(first.astype(float) - later))), 0.8)
        high = np.asarray(renderer.frame(0.4))[:, :, 3]
        self.assertFalse(high[:20].any())
        self.assertFalse(high[-20:].any())
        for t in (0.125, 0.25, 0.5, 1, 4.7):
            left, top, right, bottom = renderer.frame(t).getchannel('A').getbbox()
            for x, y in ((0.24, 0.32), (0.76, 0.6)):
                self.assertGreaterEqual(left + (x - 0.5) * 960, 0)
                self.assertLessEqual(right + (x - 0.5) * 960, 960)
                self.assertGreaterEqual(top + (y - 0.5) * 540, 0)
                self.assertLessEqual(bottom + (y - 0.5) * 540, 540)

    def test_orbital_animation_moves_and_fades_to_transparency(self):
        renderer = Renderer('prosper')
        first = np.asarray(renderer.frame(1))
        later = np.asarray(renderer.frame(2))
        self.assertGreater(int(np.count_nonzero(first != later)), 10000)
        for t in (0, DURATION):
            self.assertIsNone(renderer.frame(t).getchannel('A').getbbox())

    def test_thumbs_have_shading_padding_and_different_silhouettes(self):
        sprites = []
        for key in ('thumbs_up', 'thumbs_down'):
            renderer = Renderer(key)
            sprite = np.asarray(renderer.bubble)
            sprites.append(sprite)
            alpha = sprite[:, :, 3]
            self.assertFalse(alpha[:2].any())
            self.assertFalse(alpha[:, :2].any())
            self.assertFalse(alpha[:, -2:].any())
            hand = sprite[45:170, 70:180]
            bright = hand[:, :, 0] > 210
            self.assertGreater(int(bright.sum()), 2000)
            self.assertGreater(float(hand[:, :, 0][bright].std()), 2)
            for t in (0, DURATION):
                self.assertIsNone(renderer.frame(t).getchannel('A').getbbox())
        self.assertFalse(np.array_equal(*sprites))


if __name__ == '__main__':
    unittest.main()
