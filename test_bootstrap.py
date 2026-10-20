import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock

import bootstrap
import settings


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.home = Path(self.folder.name)
        self.patch = patch.object(Path, 'home', return_value=self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        preferences = patch.object(settings, 'SETTINGS_PATH', self.home / '.config/teams-effects/settings.json')
        preferences.start()
        self.addCleanup(preferences.stop)

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

    def test_output_profile_changes_only_when_obs_is_stopped(self):
        path = self.home / '.config/obs-studio/basic/profiles/Teams_Effects/basic.ini'
        path.parent.mkdir(parents=True)
        original = '[General]\nName=Teams Effects\n[Video]\nBaseCX=1280\nBaseCY=720\nOutputCX=1280\nOutputCY=720\n[Audio]\nSampleRate=48000\n'
        path.write_text(original)
        with patch.object(bootstrap.subprocess, 'run', return_value=Mock(returncode=0)):
            with self.assertRaisesRegex(RuntimeError, 'Close OBS'):
                bootstrap.configure_video()
        self.assertEqual(path.read_text(), original)
        with patch.object(bootstrap.subprocess, 'run', return_value=Mock(returncode=1)):
            bootstrap.configure_video()
        updated = path.read_text()
        self.assertIn('OutputCX=640', updated)
        self.assertIn('OutputCY=360', updated)
        self.assertIn('BaseCX=1280', updated)
        self.assertIn('SampleRate=48000', updated)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        with patch.object(bootstrap.subprocess, 'run') as run:
            bootstrap.configure_video()
            run.assert_not_called()
        for resolution in (540, 720):
            settings.update_settings(output_resolution=resolution)
            with patch.object(bootstrap.subprocess, 'run', return_value=Mock(returncode=1)):
                bootstrap.configure_video()
            self.assertIn(f'OutputCX={resolution * 16 // 9}', path.read_text())
            self.assertIn(f'OutputCY={resolution}', path.read_text())

    def test_generated_service_accepts_paths_with_spaces_and_specifiers(self):
        base = self.home / 'app with % and $ in name'
        (base / '.venv/bin').mkdir(parents=True)
        (base / '.venv/bin/python').symlink_to('/usr/bin/python3')
        unit = self.home / 'handspark-test.service'
        unit.write_text(bootstrap.unit_text(base))
        runtime = self.home / 'runtime'
        runtime.mkdir(mode=0o700)
        result = subprocess.run(['systemd-analyze', '--user', 'verify', str(unit)],
                                env={**os.environ, 'XDG_RUNTIME_DIR': str(runtime)},
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

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
