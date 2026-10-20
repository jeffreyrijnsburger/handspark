import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import control
from matte import soften_person
from test_gestures import hand


class MaskTests(unittest.TestCase):
    def test_person_stays_opaque_and_background_transparent(self):
        probability = np.zeros((90, 160), np.float32)
        probability[20:80, 50:110] = 1
        mask = soften_person(probability)
        self.assertGreater(mask[45, 80], 0.99)
        self.assertLess(mask[5, 5], 0.01)
        self.assertTrue(np.any((mask > 0.01) & (mask < 0.99)), 'edges should be feathered')

    def test_moving_subject_does_not_leave_a_silhouette(self):
        previous = np.ones((90, 160), np.float32)
        mask = soften_person(np.zeros_like(previous), previous=previous)
        self.assertLess(float(mask.max()), 0.01)

    def test_fingers_are_preserved_without_filling_their_gap(self):
        mask = soften_person(np.zeros((180, 320), np.float32), [hand()])
        self.assertGreater(mask[round(0.32 * 180), round(0.35 * 320)], 0.9)
        self.assertLess(mask[round(0.32 * 180), round(0.42 * 320)], 0.1)


class ControlTests(unittest.TestCase):
    def test_invalid_commands_never_reach_the_camera(self):
        server = control.Control()
        for data in ({'command': 'react', 'reaction': 'unknown'},
                     {'command': 'react', 'reaction': 'prosper'},
                     {'command': 'automatic', 'enabled': 'false'}, {'command': 'delete'}):
            self.assertFalse(server.handle(data)['ok'])
        self.assertTrue(server.commands.empty())

    def test_private_socket_and_command_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = Path(folder) / 'camera'
            with patch.object(control, 'RUNTIME', runtime), patch.object(control, 'SOCKET', runtime / 'control.sock'):
                server = control.Control()
                server.start()
                try:
                    self.assertEqual((runtime / 'control.sock').stat().st_mode & 0o777, 0o600)
                    self.assertTrue(control.request('automatic', enabled=False)['ok'])
                    self.assertEqual(server.commands.get(timeout=1), {'command': 'automatic', 'enabled': False})
                    server.update(automatic=False, preview='private-frame')
                    self.assertFalse(control.request()['automatic'])
                    self.assertNotIn('preview', control.request())
                    self.assertEqual(control.request(preview=True)['preview'], 'private-frame')
                finally:
                    server.close()
                self.assertFalse((runtime / 'control.sock').exists())


if __name__ == '__main__':
    unittest.main()
