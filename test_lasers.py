from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from laser_show import LaserShow
import render_reactions


class LaserTests(unittest.TestCase):
    def test_full_transparency_at_animation_boundaries(self):
        show = LaserShow()
        for time in (-1, 0, 5, 6):
            image = show.frame(time)
            self.assertEqual(image.mode, 'RGBA')
            self.assertEqual(image.size, (960, 540))
            self.assertIsNone(image.getchannel('A').getbbox())

    def test_choreography_moves_and_has_colored_light_across_the_stage(self):
        show = LaserShow()
        first = np.asarray(show.frame(1.1))
        later = np.asarray(show.frame(2.8))
        self.assertGreater(np.mean(np.abs(first.astype(float) - later)), 5)
        for area in (first[:, :240], first[:, 720:]):
            bright = area[:, :, :3].max(axis=2) > 200
            self.assertGreater(int(bright.sum()), 1000)
        self.assertLess(int(first[:, :, 3].min()), 150, 'haze must retain the camera background')
        self.assertTrue(np.array_equal(first, np.asarray(LaserShow().frame(1.1))), 'renders are deterministic')

    def test_updated_laser_source_invalidates_previously_rendered_clips(self):
        names = ('render_reactions.py', 'laser_show.py', 'rain_cloud.py', 'thumb_show.py', 'prosper_show.py', 'reactions.py',
                 'emoji/emoji_u1f44d.png', 'emoji/emoji_u1f44e.png')
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            for name in names:
                path = base / name
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(b'original')
            with patch.object(render_reactions, 'BASE', base):
                old = render_reactions.asset_signature()
                for source in ('laser_show.py', 'rain_cloud.py', 'thumb_show.py', 'prosper_show.py'):
                    (base / source).write_bytes(b'new effect source')
                    self.assertNotEqual(old, render_reactions.asset_signature())
                    (base / source).write_bytes(b'original')


if __name__ == '__main__':
    unittest.main()
