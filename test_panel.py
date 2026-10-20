"""Run with the system Python/PyQt5 and QT_QPA_PLATFORM=offscreen."""
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from PyQt5 import QtCore, QtGui, QtWidgets
import panel
import settings


class PanelLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'settings.json'
        self.patch = patch.object(settings, 'SETTINGS_PATH', self.path)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        settings.update_settings(language='nl')
        self.widget = panel.Panel(autostart=False, poll=False)
        self.addCleanup(self.widget.close)

    def language(self, code):
        self.widget.language_choice.setCurrentIndex(self.widget.language_choice.findData(code))
        self.app.processEvents()

    def test_live_translation_preserves_video_controls_and_progress(self):
        with patch.object(panel, 'request') as request:
            self.widget.apply_status({'automatic': True, 'depth': False, 'candidate': 'heart', 'progress': 0.4})
            self.widget.preview.image = QtGui.QPixmap(320, 180)
            self.widget.preview.image.fill(QtGui.QColor('#274c57'))
            image_key = self.widget.preview.image.cacheKey()
            self.language('en')
            self.assertEqual(self.widget.camera.text(), 'Stop camera')
            self.assertEqual(self.widget.buttons['heart'].text(), 'Hearts')
            self.assertEqual(self.widget.buttons['lasers'].toolTip(), 'Metal horns with both hands')
            self.assertEqual(self.widget.feedback.text(), 'Hold briefly: Hearts')
            self.assertTrue(self.widget.automatic.isChecked())
            self.assertFalse(self.widget.depth.isChecked())
            self.assertEqual(self.widget.progress.value(), 40)
            self.assertEqual(self.widget.preview.image.cacheKey(), image_key)
            self.assertTrue(self.widget.online)
            request.assert_not_called()

    def test_offline_language_is_saved_and_loaded_by_a_new_panel(self):
        self.assertEqual(self.widget.language, 'nl')
        self.assertTrue(self.widget.language_choice.isEnabled())
        self.language('en')
        self.assertEqual(self.widget.preview.placeholder, 'Start the camera to see a preview')
        second = panel.Panel(autostart=False, poll=False)
        self.addCleanup(second.close)
        self.assertEqual(second.language, 'en')
        self.assertEqual(second.feedback.text(), 'Camera is off.')

    def test_new_install_defaults_to_english_without_changing_existing_dutch_panel(self):
        self.path.unlink()
        fresh = panel.Panel(autostart=False, poll=False)
        self.addCleanup(fresh.close)
        self.assertEqual(fresh.language, 'en')
        self.assertEqual(fresh.language_choice.currentText(), 'English')
        self.assertEqual(self.widget.language, 'nl')

    def test_failed_save_keeps_previous_language_and_shows_error(self):
        with patch.object(panel, 'update_settings', side_effect=PermissionError('read-only')):
            self.language('en')
        self.assertEqual(self.widget.language, 'nl')
        self.assertEqual(self.widget.language_choice.currentData(), 'nl')
        self.assertIn('niet worden opgeslagen', self.widget.feedback.text())

    def test_dynamic_status_and_existing_errors_change_language(self):
        self.widget.action_error = 'command_failed'
        self.widget.error_until = time.monotonic() + 5
        self.language('en')
        self.assertEqual(self.widget.feedback.text(), 'The command failed. Please try again.')
        self.widget.action_error = None
        cases = [({'automatic': False}, 'Hand gestures are paused.'),
                 ({'needs_release': True}, 'Release the gesture'),
                 ({'cooldown': 3}, 'The next reaction'),
                 ({'reaction': 'heart'}, 'Hearts'),
                 ({'error': 'frame_unavailable', 'error_code': 'frame_unavailable'}, 'Camera image temporarily unavailable')]
        for extra, expected in cases:
            self.widget.apply_status({'automatic': True, 'depth': True, **extra})
            self.assertTrue(self.widget.feedback.text().startswith(expected))

    def test_preview_options_save_offline_and_keep_language_and_camera_state(self):
        self.widget.resolution_choice.setCurrentIndex(self.widget.resolution_choice.findData(540))
        self.widget.fps_choice.setCurrentIndex(self.widget.fps_choice.findData(24))
        values = settings.load_settings()
        self.assertEqual((values['preview_resolution'], values['preview_fps']), (540, 24))
        self.assertEqual(values['language'], 'nl')
        self.assertFalse(self.widget.online)
        self.assertEqual(self.widget.reader.process.state(), QtCore.QProcess.NotRunning)

    def test_failed_preview_save_restores_previous_choices(self):
        with patch.object(panel, 'update_settings', side_effect=PermissionError('read-only')):
            self.widget.fps_choice.setCurrentIndex(self.widget.fps_choice.findData(15))
        self.assertEqual(self.widget.fps_choice.currentData(), 30)
        self.assertIn('niet worden opgeslagen', self.widget.feedback.text())

    def test_status_poll_never_requests_screenshot_previews(self):
        with patch.object(panel, 'request', return_value={'automatic': True, 'depth': True}) as request:
            self.widget.poll()
            self.widget.pending.result(timeout=2)
            request.assert_called_once_with('status')

    def test_language_and_stop_controls_fit_wide_and_narrow_layouts(self):
        self.widget.show()
        for code in ('nl', 'en'):
            self.language(code)
            for width, height in ((760, 780), (480, 860)):
                self.widget.resize(width, height)
                self.app.processEvents()
                self.assertEqual(self.widget.width(), width)
                for control in (self.widget.language_choice, self.widget.resolution_choice, self.widget.fps_choice,
                                self.widget.camera, self.widget.cancel,
                                *self.widget.buttons.values()):
                    position = control.mapTo(self.widget, QtCore.QPoint())
                    self.assertGreaterEqual(position.x(), 0)
                    self.assertLessEqual(position.x() + control.width(), self.widget.width())
                    self.assertLessEqual(position.y() + control.height(), self.widget.height())
                    self.assertGreaterEqual(control.width(), control.minimumSizeHint().width())


if __name__ == '__main__':
    unittest.main()
