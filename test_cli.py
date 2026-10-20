import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parent


class CliTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.env = {**os.environ, 'HOME': self.folder.name, 'XDG_RUNTIME_DIR': self.folder.name + '/runtime'}

    def call(self, *args):
        return subprocess.run(['/usr/bin/python3', str(BASE / 'bin/handspark'), *args],
                              env=self.env, text=True, capture_output=True, timeout=10)

    def test_discovery_is_read_only_and_ids_are_stable(self):
        commands = self.call('commands', '--json')
        self.assertEqual(commands.returncode, 0, commands.stderr)
        data = json.loads(commands.stdout)
        self.assertEqual(data['schema_version'], 1)
        self.assertEqual(data['version'], (BASE / 'VERSION').read_text().strip())
        self.assertEqual(len(data['reactions']), 8)
        self.assertIn('lasers', data['reactions'])
        self.assertNotIn('prosper', data['reactions'])
        self.assertFalse((Path(self.folder.name) / '.config').exists())

    def test_offline_status_is_json_without_starting_a_camera(self):
        result = self.call('status', '--json')
        self.assertEqual(result.returncode, 3)
        data = json.loads(result.stdout)
        self.assertFalse(data['ok'])
        self.assertEqual(data['error_code'], 'camera_offline')
        self.assertNotIn('preview', data)
        self.assertFalse((Path(self.folder.name) / '.config').exists())

    def test_language_option_changes_labels_and_preserves_reaction_ids(self):
        self.assertEqual(json.loads(self.call('language', '--json').stdout)['language'], 'en')
        self.assertEqual(self.call('language', 'nl').returncode, 0)
        dutch = json.loads(self.call('list', '--json').stdout)['reactions']
        self.assertEqual(dutch[0]['name'], 'Hartjes')
        self.assertEqual(self.call('language', 'en').returncode, 0)
        english = json.loads(self.call('list', '--json').stdout)['reactions']
        self.assertEqual(english[0]['name'], 'Hearts')
        self.assertEqual([r['id'] for r in dutch], [r['id'] for r in english])
        self.assertEqual(json.loads(self.call('language', '--json').stdout)['language'], 'en')
        self.assertEqual(self.call('language', 'fr').returncode, 2)
        self.assertEqual(json.loads(self.call('language', '--json').stdout)['language'], 'en')

    def test_preview_configuration_is_available_offline(self):
        default = json.loads(self.call('preview', '--json').stdout)
        self.assertEqual((default['preview_resolution'], default['preview_fps']), (360, 30))
        self.assertFalse((Path(self.folder.name) / '.config').exists())
        self.call('language', 'nl')
        result = self.call('preview', '--resolution', '720', '--fps', '24', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        values = json.loads(result.stdout)
        self.assertEqual((values['preview_resolution'], values['preview_fps']), (720, 24))
        self.assertEqual(json.loads(self.call('language', '--json').stdout)['language'], 'nl')
        self.assertEqual(self.call('preview', '--fps', '60').returncode, 2)
        self.assertEqual(self.call('start', '--fps', '30').returncode, 2)

    def test_output_configuration_is_saved_without_starting_or_restarting_a_camera(self):
        default = json.loads(self.call('output', '--json').stdout)
        self.assertEqual((default['output_resolution'], default['output_fps']), (360, 30))
        self.assertFalse((Path(self.folder.name) / '.config').exists())
        self.call('language', 'nl')
        result = self.call('output', '--resolution', '540', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['output_resolution'], 540)
        self.assertTrue(json.loads(result.stdout)['applies_on_next_start'])
        self.assertEqual(json.loads(self.call('language', '--json').stdout)['language'], 'nl')
        self.assertEqual(json.loads(self.call('preview', '--json').stdout)['preview_resolution'], 360)
        self.assertEqual(self.call('output', '--fps', '15').returncode, 2)
        self.assertEqual(self.call('output', '--resolution', '1080').returncode, 2)

    def test_tray_and_closing_settings_are_readable_and_saveable_offline(self):
        defaults = json.loads(self.call('on-close', '--json').stdout)
        self.assertEqual(defaults['close_action'], 'stop')
        self.assertTrue(defaults['tray_enabled'])
        self.assertFalse((Path(self.folder.name) / '.config').exists())
        self.call('language', 'nl')
        for action in ('background', 'tray', 'stop'):
            result = self.call('on-close', action, '--json')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['close_action'], action)
        self.call('on-close', 'tray')
        disabled = json.loads(self.call('tray', 'off', '--json').stdout)
        self.assertFalse(disabled['tray_enabled'])
        self.assertEqual(disabled['close_action'], 'stop')
        enabled = json.loads(self.call('on-close', 'tray', '--json').stdout)
        self.assertTrue(enabled['tray_enabled'])
        self.assertEqual(json.loads(self.call('language', '--json').stdout)['language'], 'nl')
        self.assertEqual(self.call('on-close', 'invalid').returncode, 2)
        self.assertEqual(self.call('tray', 'invalid').returncode, 2)

    def test_start_and_restart_replace_the_launcher_instead_of_leaving_helpers(self):
        app = Path(self.folder.name) / 'app'
        (app / 'bin').mkdir(parents=True)
        (app / '.venv/bin').mkdir(parents=True)
        (app / '.venv/bin/python').symlink_to('/usr/bin/python3')
        for name in ('bin/handspark', 'controller.py', 'bootstrap.py', 'settings.py', 'i18n.py', 'reactions.py', 'VERSION'):
            (app / name).write_bytes((BASE / name).read_bytes())
        helpers = Path(self.folder.name) / 'helpers'
        helpers.mkdir()
        systemctl = helpers / 'systemctl'
        systemctl.write_text(
            '#!/usr/bin/python3\nimport json, os, pathlib, sys\n'
            'if sys.argv[2] in ("start", "restart"):\n'
            ' print(json.dumps({"pid": os.getpid(), "action": sys.argv[2]}))\n')
        systemctl.chmod(0o755)
        pgrep = helpers / 'pgrep'
        pgrep.write_text('#!/bin/sh\nexit 1\n')
        pgrep.chmod(0o755)
        env = {**self.env, 'PATH': str(helpers) + os.pathsep + os.environ['PATH']}
        for action in ('start', 'restart'):
            process = subprocess.Popen(['/usr/bin/python3', str(app / 'bin/handspark'), action],
                                       env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout), {'pid': process.pid, 'action': action})


if __name__ == '__main__':
    unittest.main()
