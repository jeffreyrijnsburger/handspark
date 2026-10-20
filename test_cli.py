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


if __name__ == '__main__':
    unittest.main()
