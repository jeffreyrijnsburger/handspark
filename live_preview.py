"""Read composed video into Qt without reserving the meeting camera device."""
from pathlib import Path

from PyQt5 import QtCore

from settings import PREVIEW_FPS, PREVIEW_RESOLUTIONS


def preview_command(resolution, fps):
    if type(resolution) is not int or resolution not in PREVIEW_RESOLUTIONS:
        raise ValueError('Unsupported preview resolution')
    if type(fps) is not int or fps not in PREVIEW_FPS:
        raise ValueError('Unsupported preview frame rate')
    base = Path(__file__).resolve().parent
    return (str(base / '.venv/bin/python'),
            [str(base / 'preview_stream.py'), '--resolution', str(resolution), '--fps', str(fps)])


class JpegFrames:
    """Return the newest complete frame, dropping backlog rather than adding latency."""
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer.extend(data)
        latest = None
        while self.buffer:
            start = self.buffer.find(b'\xff\xd8')
            if start < 0:
                self.buffer[:] = self.buffer[-1:]
                break
            if start:
                del self.buffer[:start]
            end = self.buffer.find(b'\xff\xd9', 2)
            if end < 0:
                break
            latest = bytes(self.buffer[:end + 2])
            del self.buffer[:end + 2]
        if len(self.buffer) > 4 * 1024 * 1024:
            self.buffer.clear()
        return latest


class LivePreview(QtCore.QObject):
    frame = QtCore.pyqtSignal(bytes)
    unavailable = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QtCore.QProcess(self)
        self.process.readyReadStandardOutput.connect(self.receive)
        self.process.readyReadStandardError.connect(self.discard_errors)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.failed)
        self.retry = QtCore.QTimer(self)
        self.retry.setSingleShot(True)
        self.retry.timeout.connect(self.launch)
        self.wanted = False
        self.options = (360, 30)
        self.running_options = None
        self.decoder = JpegFrames()

    def configure(self, resolution, fps):
        preview_command(resolution, fps)  # Validate before changing a running reader.
        options = (resolution, fps)
        if options == self.options:
            return
        self.options = options
        self.retry.stop()
        if self.process.state() != QtCore.QProcess.NotRunning:
            self.process.kill()
        elif self.wanted:
            self.launch()

    def start(self):
        self.wanted = True
        if self.process.state() == QtCore.QProcess.NotRunning and not self.retry.isActive():
            self.launch()

    def launch(self):
        if not self.wanted or self.process.state() != QtCore.QProcess.NotRunning:
            return
        self.decoder = JpegFrames()
        self.running_options = self.options
        program, arguments = preview_command(*self.options)
        self.process.start(program, arguments)

    def receive(self):
        data = bytes(self.process.readAllStandardOutput())
        if not self.wanted:
            return
        latest = self.decoder.feed(data)
        if latest:
            self.frame.emit(latest)

    def discard_errors(self):
        self.process.readAllStandardError()

    def failed(self, error):
        if self.wanted and error == QtCore.QProcess.FailedToStart:
            self.unavailable.emit()
            self.retry.start(1500)

    def finished(self, *_):
        self.decoder = JpegFrames()
        if not self.wanted:
            return
        if self.options != self.running_options:
            self.launch()
        else:
            self.unavailable.emit()
            self.retry.start(1500)

    def stop(self):
        self.wanted = False
        self.retry.stop()
        if self.process.state() != QtCore.QProcess.NotRunning:
            self.process.kill()
        self.decoder = JpegFrames()

    def close(self):
        self.stop()
        if self.process.state() != QtCore.QProcess.NotRunning:
            self.process.waitForFinished(500)
