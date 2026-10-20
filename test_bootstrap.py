import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import bootstrap


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.home = Path(self.folder.name)
        self.patch = patch.object(Path, 'home', return_value=self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_fresh_obs_setup_is_private_and_idempotent(self):
        with patch.object(bootstrap.subprocess, 'run', return_value=Mock(returncode=1)):
            bootstrap.configure_obs()
            password = (self.home / '.config/teams-effects/obs-password').read_text().strip()
            self.assertGreater(len(password), 30)
            config_path = self.home / '.config/obs-studio/plugin_config/obs-websocket/config.json'
            config = json.loads(config_path.read_text())
            self.assertEqual(config['server_password'], password)
            self.assertEqual(config['server_port'], 4467)
            self.assertTrue(config['auth_required'])
            self.assertEqual(config_path.stat().st_mode & 0o777, 0o600)
            scene = json.loads((self.home / '.config/obs-studio/basic/scenes/Teams_Effects.json').read_text())
            self.assertEqual(scene['sources'][0]['id'], 'scene')
            self.assertEqual(scene['virtual-camera'], {'type2': 3})
            before = config_path.read_bytes()
            bootstrap.configure_obs()
            self.assertEqual(config_path.read_bytes(), before)

    def test_running_obs_is_not_reconfigured(self):
        with patch.object(bootstrap.subprocess, 'run', return_value=Mock(returncode=0)):
            with self.assertRaisesRegex(RuntimeError, 'Close OBS'):
                bootstrap.configure_obs()
        self.assertFalse((self.home / '.config').exists())

    def test_initial_configuration_preserves_existing_obs_settings(self):
        path = self.home / '.config/obs-studio/plugin_config/obs-websocket/config.json'
        path.parent.mkdir(parents=True)
        original = '{"some_setting": "keep-me"}'
        path.write_text(original)
        with patch.object(bootstrap.subprocess, 'run', return_value=Mock(returncode=1)):
            bootstrap.configure_obs()
        config = json.loads(path.read_text())
        self.assertEqual(config['some_setting'], 'keep-me')
        self.assertEqual(path.with_suffix('.json.before-handspark').read_text(), original)


if __name__ == '__main__':
    unittest.main()
