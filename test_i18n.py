import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from string import Formatter
import tempfile
import unittest
from unittest.mock import patch

import control
from i18n import MESSAGES, translate
from reactions import REACTIONS
import settings


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'config/settings.json'
        self.patch = patch.object(settings, 'SETTINGS_PATH', self.path)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_missing_and_invalid_preferences_keep_dutch_default(self):
        self.assertEqual(settings.load_settings()['language'], 'nl')
        self.path.parent.mkdir()
        for value in ('not json', '[]', '{"language": "fr"}', '{"language": []}'):
            self.path.write_text(value)
            self.assertEqual(settings.load_settings()['language'], 'nl')

    def test_camera_settings_preserve_language_and_other_preferences(self):
        settings.update_settings(automatic=False, depth=True, language='en')
        settings.update_settings(depth=False)
        values = json.loads(self.path.read_text())
        self.assertEqual(values, {'automatic': False, 'depth': False, 'language': 'en'})
        settings.update_settings(language='nl')
        self.assertFalse(settings.load_settings()['automatic'])
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_invalid_changes_never_overwrite_preferences(self):
        settings.update_settings(language='en')
        for change in ({'language': 'fr'}, {'language': []}, {'depth': 'false'}, {'unknown': True}):
            with self.assertRaises(ValueError):
                settings.update_settings(**change)
        self.assertEqual(settings.load_settings()['language'], 'en')

    def test_simultaneous_camera_and_language_changes_are_merged(self):
        changes = [{'automatic': False}, {'depth': False}, {'language': 'en'}] * 10
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(lambda change: settings.update_settings(**change), changes))
        self.assertEqual(settings.load_settings(), {'automatic': False, 'depth': False, 'language': 'en'})

    def test_control_errors_use_current_language_without_restarting_camera(self):
        runtime = Path(self.folder.name) / 'runtime'
        with patch.object(control, 'RUNTIME', runtime), patch.object(control, 'SOCKET', runtime / 'control.sock'):
            server = control.Control()
            server.start()
            try:
                settings.update_settings(language='en')
                with self.assertRaisesRegex(RuntimeError, 'Unknown reaction'):
                    control.request('react', reaction='invalid')
                settings.update_settings(language='nl')
                with self.assertRaisesRegex(RuntimeError, 'Onbekende reactie'):
                    control.request('react', reaction='invalid')
                self.assertTrue(server.commands.empty())
            finally:
                server.close()


class TranslationTests(unittest.TestCase):
    def test_complete_languages_and_matching_placeholders(self):
        self.assertEqual(set(MESSAGES['nl']), set(MESSAGES['en']))
        formatter = Formatter()
        for key in MESSAGES['nl']:
            fields = lambda message: {field for _, field, _, _ in formatter.parse(message) if field}
            self.assertEqual(fields(MESSAGES['nl'][key]), fields(MESSAGES['en'][key]), key)
        for reaction in REACTIONS:
            for language in ('nl', 'en'):
                self.assertIn('reaction.' + reaction, MESSAGES[language])
                self.assertIn('gesture.' + reaction, MESSAGES[language])

    def test_unknown_language_falls_back_to_dutch(self):
        self.assertEqual(translate('fr', 'camera_start'), 'Camera starten')
        self.assertEqual(translate('en', 'external error {raw}'), 'external error {raw}')


if __name__ == '__main__':
    unittest.main()
