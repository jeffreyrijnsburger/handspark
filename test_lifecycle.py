"""Shutdown owns only its OBS child; no camera or OBS installation is needed."""
import subprocess
import sys
import unittest
from unittest.mock import Mock

import controller
from matte import PersonMatte


class ObsShutdownTests(unittest.TestCase):
    def test_stops_video_before_quitting_owned_obs(self):
        events = []
        obs, child = Mock(), Mock()
        child.poll.return_value = None
        obs.call.side_effect = lambda kind: events.append(kind)
        obs.close.side_effect = lambda: events.append('disconnect')
        child.terminate.side_effect = lambda: events.append('terminate')
        controller.shutdown_obs(obs, child)
        self.assertEqual(events, ['StopVirtualCam', 'disconnect', 'terminate'])
        child.wait.assert_called_once_with(timeout=8)
        child.kill.assert_not_called()

    def test_lost_connection_still_terminates_a_real_child(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        self.addCleanup(lambda: child.poll() is None and child.kill())
        obs = Mock()
        obs.call.side_effect = controller.websocket.WebSocketConnectionClosedException('closed')
        obs.close.side_effect = OSError('closed')
        controller.shutdown_obs(obs, child)
        self.assertIsNotNone(child.poll())

    def test_hung_child_is_killed_with_bounded_waits(self):
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired('obs', 8), 0]
        controller.shutdown_obs(None, child)
        child.terminate.assert_called_once()
        child.kill.assert_called_once()
        self.assertEqual([call.kwargs['timeout'] for call in child.wait.call_args_list], [8, 2])

    def test_unexpected_disconnect_error_cannot_skip_owned_child_cleanup(self):
        obs, child = Mock(), Mock()
        child.poll.return_value = None
        obs.close.side_effect = RuntimeError('disconnect failed')
        with self.assertRaisesRegex(RuntimeError, 'disconnect failed'):
            controller.shutdown_obs(obs, child)
        child.terminate.assert_called_once()
        child.wait.assert_called_once_with(timeout=8)

    def test_attached_obs_is_left_running(self):
        obs = Mock()
        controller.shutdown_obs(obs, None)
        obs.call.assert_called_once_with('StopVirtualCam')
        obs.close.assert_called_once()

    def test_rejected_obs_profile_is_not_modified(self):
        obs = Mock()
        controller.shutdown_obs(obs, None, stop_camera=False)
        obs.call.assert_not_called()
        obs.close.assert_called_once()

    def test_mask_model_is_closed_even_when_obs_is_already_gone(self):
        matte = PersonMatte.__new__(PersonMatte)
        matte.show = Mock(side_effect=OSError('closed'))
        matte.model = Mock()
        with self.assertRaises(OSError):
            matte.close()
        matte.model.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
