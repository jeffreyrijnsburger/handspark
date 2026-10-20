"""Run with the system Python/PyQt5 and QT_QPA_PLATFORM=offscreen."""
from pathlib import Path
import subprocess
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
        self.widget = panel.Panel(autostart=False, poll=False, manage_service=False)
        self.addCleanup(self.widget.close)

    def language(self, code):
        self.widget.language_choice.setCurrentIndex(self.widget.language_choice.findData(code))
        self.app.processEvents()

    def test_tray_advertises_visible_pixels_at_small_and_high_density_sizes(self):
        icon = self.widget.tray.icon()
        sizes = {(size.width(), size.height()) for size in icon.availableSizes()}
        for edge in (16, 22, 24, 32, 44, 48, 64, 128):
            with self.subTest(edge=edge):
                self.assertIn((edge, edge), sizes, 'The tray host must receive a concrete size')
                image = icon.pixmap(edge, edge).toImage()
                self.assertFalse(image.isNull())
                self.assertGreater(image.pixelColor(image.width() // 2, image.height() // 2).alpha(), 0)
                self.assertEqual(image.pixelColor(0, 0).alpha(), 0, 'Keep the logo background transparent')

    def test_live_translation_preserves_video_controls_and_progress(self):
        with patch.object(panel, 'request') as request:
            self.widget.apply_status({'automatic': True, 'depth': False, 'candidate': 'heart', 'progress': 0.4})
            self.widget.preview.image = QtGui.QPixmap(320, 180)
            self.widget.preview.image.fill(QtGui.QColor('#274c57'))
            image_key = self.widget.preview.image.cacheKey()
            self.language('en')
            self.assertEqual(self.widget.camera.text(), 'Turn camera off')
            self.assertIn('virtual camera', self.widget.camera.toolTip())
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
        self.assertEqual(self.widget.preview.placeholder, 'Turn the camera on to see a preview')
        self.assertEqual(self.widget.camera.text(), 'Turn camera on')
        self.assertNotIn('Stops', self.widget.camera.toolTip())
        second = panel.Panel(autostart=False, poll=False, manage_service=False)
        self.addCleanup(second.close)
        self.assertEqual(second.language, 'en')
        self.assertEqual(second.feedback.text(), 'Camera is off.')

    def test_new_install_defaults_to_english_without_changing_existing_dutch_panel(self):
        self.path.unlink()
        fresh = panel.Panel(autostart=False, poll=False, manage_service=False)
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

    def test_output_saves_offline_without_changing_preview_or_language(self):
        with patch.object(self.widget.process, 'start') as start:
            self.widget.output_choice.setCurrentIndex(self.widget.output_choice.findData(720))
            start.assert_not_called()
        values = settings.load_settings()
        self.assertEqual(values['output_resolution'], 720)
        self.assertEqual(values['preview_resolution'], 360)
        self.assertEqual(values['language'], 'nl')

    def test_online_output_change_restarts_camera_and_preserves_preferences(self):
        self.widget.apply_status({'automatic': True, 'depth': True})
        with patch.object(self.widget.process, 'start') as start:
            self.widget.output_choice.setCurrentIndex(self.widget.output_choice.findData(540))
            self.assertEqual(start.call_args.args[1][-1], 'restart')
        self.assertEqual(settings.load_settings()['output_resolution'], 540)
        self.assertFalse(self.widget.output_choice.isEnabled())
        self.widget.process_finished(0, QtCore.QProcess.NormalExit)
        self.assertTrue(self.widget.output_choice.isEnabled())

    def test_failed_output_save_restores_previous_choice(self):
        with patch.object(panel, 'update_settings', side_effect=PermissionError('read-only')):
            self.widget.output_choice.setCurrentIndex(self.widget.output_choice.findData(720))
        self.assertEqual(self.widget.output_choice.currentData(), 360)
        self.assertIn('niet worden opgeslagen', self.widget.feedback.text())

    def test_status_poll_never_requests_screenshot_previews(self):
        with patch.object(panel, 'request', return_value={'automatic': True, 'depth': True}) as request:
            self.widget.poll()
            self.widget.pending.result(timeout=2)
            request.assert_called_once_with('status')

    def test_closing_preferences_save_offline_and_preserve_other_settings(self):
        self.widget.close_choice.setCurrentIndex(self.widget.close_choice.findData('background'))
        self.assertEqual(settings.load_settings()['close_action'], 'background')
        self.assertIn('camera aan', self.widget.foot.text())
        values = settings.load_settings()
        self.assertEqual(values['language'], 'nl')
        self.assertEqual(values['output_resolution'], 360)
        self.assertFalse(self.widget.online)

    def test_failed_close_preference_save_restores_selection(self):
        with patch.object(panel, 'update_settings', side_effect=PermissionError('read-only')):
            self.widget.close_choice.setCurrentIndex(self.widget.close_choice.findData('background'))
        self.assertEqual(self.widget.close_choice.currentData(), 'stop')
        self.assertEqual(settings.load_settings()['close_action'], 'stop')
        self.assertIn('niet worden opgeslagen', self.widget.feedback.text())

    def test_language_and_stop_controls_fit_wide_and_narrow_layouts(self):
        self.widget.show()
        for code in ('nl', 'en'):
            self.language(code)
            for width, height in ((760, 780), (480, 860)):
                self.widget.resize(width, height)
                self.app.processEvents()
                self.assertEqual(self.widget.width(), width)
                for control in (self.widget.language_choice, self.widget.resolution_choice, self.widget.fps_choice,
                                self.widget.output_choice, self.widget.close_choice, self.widget.tray_choice,
                                self.widget.camera, self.widget.cancel,
                                *self.widget.buttons.values()):
                    position = control.mapTo(self.widget, QtCore.QPoint())
                    self.assertGreaterEqual(position.x(), 0)
                    self.assertLessEqual(position.x() + control.width(), self.widget.width())
                    self.assertLessEqual(position.y() + control.height(), self.widget.height())
                    self.assertGreaterEqual(control.width(), control.minimumSizeHint().width())


class PanelShutdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        preferences = patch.object(settings, 'SETTINGS_PATH', self.base / 'settings.json')
        preferences.start()
        self.addCleanup(preferences.stop)
        self.launcher = self.base / 'launcher.py'
        self.write_launcher()
        launcher = patch.object(panel, 'launcher_path', return_value=self.launcher)
        launcher.start()
        self.addCleanup(launcher.stop)
        self.widget = panel.Panel(autostart=False, poll=False)
        self.addCleanup(self.cleanup_widget)
        self.widget.show()
        self.app.processEvents()

    def write_launcher(self, stop_result=0):
        self.launcher.write_text(
            'import pathlib, sys, time\n'
            'base = pathlib.Path(__file__).parent\n'
            'action = sys.argv[1]\n'
            'with (base / "actions").open("a") as log: log.write(action + "\\n")\n'
            'time.sleep(30 if action in ("start", "restart") else 0.15)\n'
            f'sys.exit({stop_result})\n')

    def cleanup_widget(self):
        for process in (self.widget.process, self.widget.shutdown_process):
            if process.state() != QtCore.QProcess.NotRunning:
                process.kill()
                process.waitForFinished(1000)
        self.widget.manage_service = False
        self.widget.close()

    def wait_until(self, predicate):
        deadline = time.monotonic() + 4
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.005)
        self.assertTrue(predicate())

    def actions(self):
        path = self.base / 'actions'
        return path.read_text().splitlines() if path.exists() else []

    def test_close_waits_for_stop_and_remains_responsive(self):
        self.widget.apply_status({'automatic': True, 'depth': True})
        self.assertFalse(self.widget.close())
        self.assertTrue(self.widget.closing)
        self.assertTrue(self.widget.isVisible())
        self.assertFalse(self.widget.isEnabled())
        self.assertFalse(self.widget.reader.wanted)
        tick = []
        QtCore.QTimer.singleShot(0, lambda: tick.append(True))
        self.widget.close()  # A repeated close must not submit another stop.
        self.wait_until(lambda: not self.widget.isVisible())
        self.assertTrue(tick)
        self.assertTrue(self.widget.close_ready)
        self.assertEqual(self.actions(), ['stop'])

    def test_offline_status_still_stops_the_service_before_closing(self):
        self.assertFalse(self.widget.online)
        self.widget.close()
        self.wait_until(lambda: not self.widget.isVisible())
        self.assertEqual(self.actions(), ['stop'])

    def test_close_during_start_or_restart_cancels_launch_before_stop(self):
        for action in ('start', 'restart'):
            with self.subTest(action=action):
                if action == 'restart':
                    self.widget.close_ready = False
                    self.widget.closing = False
                    self.widget.setEnabled(True)
                    self.widget.show()
                self.widget.process.start(panel.sys.executable, [str(self.launcher), action])
                self.wait_until(lambda: action in self.actions())
                self.widget.close()
                # Late startup/status callbacks cannot restart video or preview.
                self.widget.start_camera()
                self.widget.apply_status({'automatic': True, 'depth': True})
                self.wait_until(lambda: not self.widget.isVisible())
                self.assertEqual(self.widget.process.state(), QtCore.QProcess.NotRunning)
                self.assertFalse(self.widget.reader.wanted)
        self.assertEqual(self.actions(), ['start', 'stop', 'restart', 'stop'])

    def test_failed_stop_keeps_window_available_and_close_retries(self):
        self.write_launcher(stop_result=1)
        self.widget.close()
        self.wait_until(lambda: not self.widget.closing)
        self.assertTrue(self.widget.isVisible())
        self.assertTrue(self.widget.isEnabled())
        self.assertFalse(self.widget.close_ready)
        self.assertIn('could not be turned off', self.widget.feedback.text())
        self.write_launcher()
        self.widget.close()
        self.wait_until(lambda: not self.widget.isVisible())
        self.assertEqual(self.actions(), ['stop', 'stop'])

    def test_missing_runtime_keeps_window_available_for_retry(self):
        with patch.object(panel.sys, 'executable', str(self.base / 'missing-python')):
            self.widget.close()
            self.wait_until(lambda: not self.widget.closing)
        self.assertTrue(self.widget.isVisible())
        self.assertTrue(self.widget.isEnabled())
        self.assertFalse(self.widget.close_ready)

    def test_background_close_does_not_stop_the_camera(self):
        self.widget.apply_close_preferences('background', False)
        self.assertTrue(self.widget.close())
        self.assertFalse(self.widget.isVisible())
        self.assertEqual(self.actions(), [])

    def test_hide_to_tray_then_open_and_explicit_quit(self):
        self.widget.tray_available = True
        self.widget.apply_close_preferences('tray', True)
        self.assertFalse(self.widget.close())
        self.assertFalse(self.widget.isVisible())
        self.assertFalse(self.widget.closing)
        self.assertEqual(self.actions(), [])
        self.widget.tray_open.trigger()
        self.assertTrue(self.widget.isVisible())
        self.widget.tray_quit.trigger()
        self.wait_until(lambda: not self.widget.isVisible())
        self.assertEqual(self.actions(), ['stop'])

    def test_missing_tray_falls_back_to_stopping_instead_of_hiding(self):
        self.widget.tray_available = False
        self.widget.apply_close_preferences('tray', True)
        self.widget.close()
        self.wait_until(lambda: not self.widget.isVisible())
        self.assertTrue(self.widget.close_ready)
        self.assertEqual(self.actions(), ['stop'])

    def test_disabling_tray_restores_hidden_window_and_safe_close_action(self):
        self.widget.tray_available = True
        self.widget.save_close_preferences(close_action='tray', tray_enabled=True)
        self.widget.close()
        self.assertFalse(self.widget.isVisible())
        self.widget.change_tray(False)
        self.assertTrue(self.widget.isVisible())
        self.assertEqual(settings.load_settings()['close_action'], 'stop')
        self.assertFalse(settings.load_settings()['tray_enabled'])

    def test_quit_always_stops_even_when_close_is_configured_for_background(self):
        self.widget.apply_close_preferences('background', True)
        self.widget.quit_application()
        self.wait_until(lambda: not self.widget.isVisible())
        self.assertEqual(self.actions(), ['stop'])

    def test_background_close_finishes_inflight_start_without_killing_it(self):
        self.launcher.write_text(self.launcher.read_text().replace('30 if action', '0.2 if action'))
        self.widget.apply_close_preferences('background', False)
        self.widget.start_camera()
        self.wait_until(lambda: 'start' in self.actions())
        self.widget.close()
        self.wait_until(lambda: not self.widget.isVisible())
        self.assertEqual(self.widget.process.exitCode(), 0)
        self.assertEqual(self.actions(), ['start'])

    def test_losing_tray_restores_hidden_window_without_touching_camera(self):
        self.widget.tray_available = True
        settings.update_settings(close_action='tray', tray_enabled=True)
        self.widget.apply_close_preferences('tray', True)
        self.widget.close()
        with patch.object(panel.QtWidgets.QSystemTrayIcon, 'isSystemTrayAvailable', return_value=False), \
                patch.object(panel, 'request', return_value={'automatic': True, 'depth': True}):
            self.widget.poll()
            self.widget.pending.result(timeout=2)
        self.assertTrue(self.widget.isVisible())
        self.assertEqual(self.actions(), [])

    def test_hidden_panel_keeps_the_application_event_loop_running(self):
        script = self.base / 'tray_loop.py'
        marker = self.base / 'timer-fired'
        script.write_text(
            'import sys\n'
            f'sys.path.insert(0, {str(Path(panel.__file__).parent)!r})\n'
            'from pathlib import Path\n'
            'from PyQt5 import QtCore, QtWidgets\n'
            'import panel, settings\n'
            f'settings.SETTINGS_PATH = Path({str(self.base / "child-settings.json")!r})\n'
            'app = QtWidgets.QApplication([])\n'
            'window = panel.Panel(autostart=False, poll=False)\n'
            'window.tray_available = True\n'
            'window.apply_close_preferences("tray", True)\n'
            'window.show()\n'
            'def finish():\n'
            '    assert not window.isVisible()\n'
            f'    Path({str(marker)!r}).touch()\n'
            '    window.manage_service = False\n'
            '    window.close()\n'
            '    app.quit()\n'
            'QtCore.QTimer.singleShot(0, window.close)\n'
            'QtCore.QTimer.singleShot(100, finish)\n'
            'app.exec_()\n')
        result = subprocess.run([panel.sys.executable, str(script)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(marker.exists(), 'Hiding to tray must not quit the application')


if __name__ == '__main__':
    unittest.main()
