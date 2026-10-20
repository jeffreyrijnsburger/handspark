"""Qt preview framing and process lifecycle; no physical camera is required."""
import unittest
import shutil
from unittest.mock import patch

from PyQt5 import QtCore, QtGui, QtWidgets
from live_preview import JpegFrames, LivePreview, ffmpeg_arguments


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def jpeg(self, color):
        image = QtGui.QImage(16, 9, QtGui.QImage.Format_RGB32)
        image.fill(QtGui.QColor(color))
        data = QtCore.QByteArray()
        buffer = QtCore.QBuffer(data)
        buffer.open(QtCore.QIODevice.WriteOnly)
        image.save(buffer, 'JPEG')
        return bytes(data)

    def test_split_jpegs_are_reassembled_and_backlog_is_dropped(self):
        first, latest = self.jpeg('red'), self.jpeg('blue')
        decoder = JpegFrames()
        self.assertIsNone(decoder.feed(b'noise' + first[:1]))
        self.assertIsNone(decoder.feed(first[1:100]))
        self.assertEqual(decoder.feed(first[100:] + latest), latest)
        image = QtGui.QImage.fromData(decoder.feed(first), 'JPEG')
        self.assertGreater(image.pixelColor(0, 0).red(), 200)
        self.assertFalse(decoder.buffer)

    def test_incomplete_stream_has_bounded_memory(self):
        decoder = JpegFrames()
        self.assertIsNone(decoder.feed(b'\xff\xd8' + b'x' * (5 * 1024 * 1024)))
        self.assertFalse(decoder.buffer)
        self.assertEqual(decoder.feed(self.jpeg('green')), self.jpeg('green'))

    def test_scaling_and_fps_apply_to_pipe_not_capture_device(self):
        arguments = ffmpeg_arguments('/dev/video42', 540, 24)
        self.assertIn('scale=960:540:flags=fast_bilinear,fps=24', arguments)
        self.assertNotIn('-framerate', arguments)
        self.assertNotIn('-video_size', arguments)
        self.assertEqual(arguments[-1], 'pipe:1')
        with self.assertRaises(ValueError):
            ffmpeg_arguments('/dev/video42', 1080, 30)

    def test_reconfiguration_and_stop_do_not_leave_a_reader_running(self):
        reader = LivePreview()
        self.addCleanup(reader.close)
        with patch.object(reader.process, 'state', return_value=QtCore.QProcess.Running), \
                patch.object(reader.process, 'kill') as kill:
            reader.wanted = True
            reader.configure(720, 24)
            kill.assert_called_once()
        with patch.object(reader.process, 'start') as start:
            reader.finished()
            start.assert_called_once()
        reader.stop()
        self.assertFalse(reader.wanted)
        self.assertFalse(reader.retry.isActive())

    @unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg is required for the pipe integration test')
    def test_real_video_pipe_delivers_frames_without_status_polling(self):
        reader = LivePreview()
        loop = QtCore.QEventLoop()
        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        frames = []
        def receive(data):
            image = QtGui.QImage.fromData(data, 'JPEG')
            if not image.isNull():
                frames.append(image.size())
            if len(frames) >= 25:
                loop.quit()
        reader.frame.connect(receive)
        arguments = ['-nostdin', '-v', 'error', '-re', '-f', 'lavfi',
                     '-i', 'testsrc=size=160x90:rate=30', '-t', '2',
                     '-c:v', 'mjpeg', '-threads', '1', '-f', 'image2pipe', 'pipe:1']
        try:
            with patch('live_preview.ffmpeg_arguments', return_value=arguments):
                reader.start()
                timer.start(5000)
                loop.exec_()
            self.assertGreaterEqual(len(frames), 25)
            self.assertEqual(frames[-1], QtCore.QSize(160, 90))
        finally:
            timer.stop()
            reader.close()


if __name__ == '__main__':
    unittest.main()
