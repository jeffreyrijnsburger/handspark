"""Native KDE/Qt controls and a preview of the actual Teams video output."""
import base64
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sys
import time

from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets

from control import request
from i18n import translate
from live_preview import LivePreview
from reactions import REACTIONS
from settings import LANGUAGES, PREVIEW_FPS, PREVIEW_RESOLUTIONS, load_settings, update_settings


def launcher_path():
    bundled = Path(__file__).parent / 'bin/handspark'
    return bundled if bundled.exists() else Path.home() / '.local/bin/teams-effects'


class Preview(QtWidgets.QWidget):
    def __init__(self, language):
        super().__init__()
        self.placeholder = translate(language, 'preview_placeholder')
        self.image = QtGui.QPixmap()
        self.setMinimumSize(320, 180)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), self.palette().brush(QtGui.QPalette.Base))
        if self.image.isNull():
            painter.setPen(self.palette().color(QtGui.QPalette.Text))
            painter.drawText(self.rect(), QtCore.Qt.AlignCenter, self.placeholder)
        else:
            scaled = self.image.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            painter.drawPixmap((self.width() - scaled.width()) // 2,
                               (self.height() - scaled.height()) // 2, scaled)


class Panel(QtWidgets.QWidget):
    def __init__(self, autostart=True, poll=True):
        super().__init__()
        preferences = load_settings()
        self.language = preferences['language']
        self.preview_options = (preferences['preview_resolution'], preferences['preview_fps'])
        self.live_preview = poll
        self.preview_error = False
        self.setWindowIcon(QtGui.QIcon(str(Path(__file__).parent / 'icons/handspark.svg')))
        self.resize(760, 780)
        self.setMinimumSize(480, 700)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.pending = None
        self.actions = []
        self.expected = {}
        self.action_error = None
        self.error_until = 0.0
        self.online = False
        self.starting = autostart
        self.last_state = {}
        self.buttons = {}
        self.columns = 0
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 20)
        outer.setSpacing(12)
        header = QtWidgets.QHBoxLayout()
        self.title = QtWidgets.QLabel()
        font = self.title.font()
        font.setPointSize(font.pointSize() + 3)
        font.setWeight(QtGui.QFont.DemiBold)
        self.title.setFont(font)
        header.addWidget(self.title, 1)
        self.camera = QtWidgets.QPushButton()
        self.camera.setMinimumHeight(36)
        self.camera.clicked.connect(self.toggle_camera)
        header.addWidget(self.camera)
        outer.addLayout(header)
        self.guide = QtWidgets.QLabel()
        self.guide.setWordWrap(True)
        outer.addWidget(self.guide)
        self.preview = Preview(self.language)
        outer.addWidget(self.preview, 1)
        self.reader = LivePreview(self)
        self.reader.frame.connect(self.preview_frame)
        self.reader.unavailable.connect(self.preview_failed)
        preview_row = QtWidgets.QHBoxLayout()
        self.preview_label = QtWidgets.QLabel()
        self.resolution_choice = QtWidgets.QComboBox()
        self.fps_choice = QtWidgets.QComboBox()
        for height in PREVIEW_RESOLUTIONS:
            self.resolution_choice.addItem(f'{height}p ({height * 16 // 9}×{height})', height)
        for fps in PREVIEW_FPS:
            self.fps_choice.addItem(f'{fps} fps', fps)
        self.resolution_choice.currentIndexChanged.connect(self.change_preview)
        self.fps_choice.currentIndexChanged.connect(self.change_preview)
        self.preview_label.setBuddy(self.resolution_choice)
        preview_row.addWidget(self.preview_label)
        preview_row.addWidget(self.resolution_choice)
        preview_row.addWidget(self.fps_choice)
        preview_row.addStretch()
        outer.addLayout(preview_row)
        switches = QtWidgets.QHBoxLayout()
        self.automatic = QtWidgets.QCheckBox()
        self.automatic.toggled.connect(lambda enabled: self.command('automatic', enabled=enabled))
        switches.addWidget(self.automatic)
        self.depth = QtWidgets.QCheckBox()
        self.depth.toggled.connect(lambda enabled: self.command('depth', enabled=enabled))
        switches.addWidget(self.depth)
        switches.addStretch()
        outer.addLayout(switches)
        self.feedback = QtWidgets.QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setMinimumHeight(36)
        outer.addWidget(self.feedback)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(5)
        policy = self.progress.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.progress.setSizePolicy(policy)
        self.progress.hide()
        outer.addWidget(self.progress)
        row = QtWidgets.QHBoxLayout()
        self.reaction_prompt = QtWidgets.QLabel()
        row.addWidget(self.reaction_prompt, 1)
        self.cancel = QtWidgets.QPushButton()
        self.cancel.clicked.connect(lambda: self.command('cancel'))
        self.cancel.setEnabled(False)
        row.addWidget(self.cancel)
        outer.addLayout(row)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)
        for key in REACTIONS:
            button = QtWidgets.QPushButton()
            asset = Path(__file__).parent / 'icons' / (key + '.svg')
            if key in ('thumbs_up', 'thumbs_down'):
                asset = Path(__file__).parent / 'emoji' / ('emoji_u1f44d.png' if key == 'thumbs_up' else 'emoji_u1f44e.png')
            button.setIcon(QtGui.QIcon(str(asset)))
            button.setIconSize(QtCore.QSize(24, 24))
            button.setMinimumHeight(42)
            button.clicked.connect(lambda checked=False, reaction=key: self.command('react', reaction=reaction))
            self.buttons[key] = button
        outer.addLayout(self.grid)
        self.reflow()
        self.foot = QtWidgets.QLabel()
        self.foot.setWordWrap(True)
        outer.addWidget(self.foot)
        language_row = QtWidgets.QHBoxLayout()
        self.language_label = QtWidgets.QLabel()
        self.language_choice = QtWidgets.QComboBox()
        for code, name in LANGUAGES.items():
            self.language_choice.addItem(name, code)
        self.language_label.setBuddy(self.language_choice)
        self.language_choice.currentIndexChanged.connect(self.change_language)
        language_row.addWidget(self.language_label)
        language_row.addWidget(self.language_choice)
        language_row.addStretch()
        version = (Path(__file__).parent / 'VERSION').read_text().strip()
        language_row.addWidget(QtWidgets.QLabel('HandSpark ' + version))
        outer.addLayout(language_row)
        self.process = QtCore.QProcess(self)
        self.process.finished.connect(self.process_finished)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.retranslate()
        self.apply_preview_options(*self.preview_options)
        self.apply_offline()
        if poll:
            self.timer.start(400)
        if autostart:
            QtCore.QTimer.singleShot(0, self.start_camera)

    def text(self, key, **values):
        return translate(self.language, key, **values)

    def retranslate(self):
        self.setWindowTitle(self.text('window_title'))
        self.title.setText(self.text('title'))
        self.guide.setText(self.text('guide'))
        self.camera.setText(self.text('camera_stop' if self.online else 'camera_start'))
        self.automatic.setText(self.text('automatic'))
        self.automatic.setToolTip(self.text('automatic_help'))
        self.depth.setText(self.text('depth'))
        self.depth.setToolTip(self.text('depth_help'))
        self.reaction_prompt.setText(self.text('reaction_prompt'))
        self.cancel.setText(self.text('cancel'))
        self.foot.setText(self.text('foot'))
        self.language_label.setText(self.text('language'))
        self.language_choice.setAccessibleName(self.text('language'))
        self.language_choice.setToolTip(self.text('language_help'))
        self.preview_label.setText(self.text('preview_settings'))
        self.resolution_choice.setAccessibleName(self.text('preview_resolution'))
        self.fps_choice.setAccessibleName(self.text('preview_fps'))
        self.resolution_choice.setToolTip(self.text('preview_settings_help'))
        self.fps_choice.setToolTip(self.text('preview_settings_help'))
        blocker = QtCore.QSignalBlocker(self.language_choice)
        self.language_choice.setCurrentIndex(self.language_choice.findData(self.language))
        del blocker
        for key, button in self.buttons.items():
            button.setText(self.text('reaction.' + key))
            button.setAccessibleName(self.text('reaction.' + key))
            button.setToolTip(self.text('gesture.' + key))
        self.preview.placeholder = self.text('preview_placeholder')
        self.preview.update()
        self.render_feedback()

    def change_language(self, index):
        language = self.language_choice.itemData(index)
        if language not in LANGUAGES or language == self.language:
            return
        try:
            update_settings(language=language)
        except OSError:
            self.action_error = 'language_save_failed'
            self.error_until = time.monotonic() + 5
        else:
            self.language = language
            if self.action_error == 'language_save_failed':
                self.action_error = None
        self.retranslate()

    def apply_preview_options(self, resolution, fps):
        self.preview_options = (resolution, fps)
        for control, value in ((self.resolution_choice, resolution), (self.fps_choice, fps)):
            blocker = QtCore.QSignalBlocker(control)
            control.setCurrentIndex(control.findData(value))
            del blocker
        self.reader.configure(resolution, fps)

    def change_preview(self, _index):
        resolution, fps = self.resolution_choice.currentData(), self.fps_choice.currentData()
        if resolution is None or fps is None:
            return
        try:
            update_settings(preview_resolution=resolution, preview_fps=fps)
        except OSError:
            self.action_error = 'preview_save_failed'
            self.error_until = time.monotonic() + 5
            self.apply_preview_options(*self.preview_options)
        else:
            self.apply_preview_options(resolution, fps)
            if self.action_error == 'preview_save_failed':
                self.action_error = None
        self.render_feedback()

    def preview_frame(self, data):
        image = QtGui.QPixmap()
        if not image.loadFromData(data, 'JPEG'):
            return
        self.preview.image = image
        self.preview.update()
        if self.preview_error:
            self.preview_error = False
            self.render_feedback()

    def preview_failed(self):
        self.preview_error = True
        self.render_feedback()

    def reflow(self):
        columns = 2 if self.width() < 680 else 4
        if columns == self.columns:
            return
        self.columns = columns
        for button in self.buttons.values():
            self.grid.removeWidget(button)
        for i, button in enumerate(self.buttons.values()):
            self.grid.addWidget(button, i // columns, i % columns)

    def resizeEvent(self, event):
        self.reflow()
        super().resizeEvent(event)

    def start_camera(self):
        if self.process.state() != QtCore.QProcess.NotRunning:
            return
        self.starting = True
        self.action_error = None
        self.camera.setEnabled(False)
        self.render_feedback()
        self.process.start(sys.executable, [str(launcher_path()), 'start'])

    def toggle_camera(self):
        if self.online:
            self.starting = False
            self.camera.setEnabled(False)
            self.process.start(sys.executable, [str(launcher_path()), 'stop'])
        else:
            self.start_camera()

    def process_finished(self, exit_code, exit_status):
        self.starting = False
        self.camera.setEnabled(True)
        if exit_code:
            self.action_error = 'camera_failed'
            self.error_until = time.monotonic() + 3600
            self.render_feedback()
        self.poll()

    def command(self, command, **values):
        if not self.online:
            return
        if command in ('automatic', 'depth'):
            self.expected[command] = (values['enabled'], time.monotonic() + 2)
        self.actions.append(self.executor.submit(request, command, **values))

    def poll(self):
        preferences = load_settings()
        language = preferences['language']
        if language != self.language:
            self.language = language
            self.retranslate()
        options = (preferences['preview_resolution'], preferences['preview_fps'])
        if options != self.preview_options:
            self.apply_preview_options(*options)
        for action in self.actions[:]:
            if action.done():
                self.actions.remove(action)
                try:
                    action.result()
                except (OSError, ValueError, RuntimeError):
                    self.action_error = 'command_failed'
                    self.error_until = time.monotonic() + 5
        if self.pending is not None:
            if not self.pending.done():
                return
            try:
                self.apply_status(self.pending.result())
            except (OSError, ValueError, RuntimeError):
                self.apply_offline()
            self.pending = None
        self.pending = self.executor.submit(request, 'status')

    def apply_offline(self):
        self.online = False
        self.reader.stop()
        self.preview_error = False
        self.last_state = {}
        self.camera.setText(self.text('camera_start'))
        self.camera.setEnabled(not self.starting)
        for control in (*self.buttons.values(), self.automatic, self.depth, self.cancel):
            control.setEnabled(False)
        self.preview.image = QtGui.QPixmap()
        self.preview.update()
        self.progress.hide()
        self.render_feedback()

    def apply_status(self, state):
        self.online = True
        if self.live_preview:
            self.reader.start()
        self.last_state = state
        self.camera.setText(self.text('camera_stop'))
        self.camera.setEnabled(True)
        for control in (*self.buttons.values(), self.automatic, self.depth):
            control.setEnabled(True)
        for key, control in (('automatic', self.automatic), ('depth', self.depth)):
            value = state[key]
            expected = self.expected.get(key)
            if expected:
                if value == expected[0] or time.monotonic() >= expected[1]:
                    self.expected.pop(key, None)
                else:
                    value = expected[0]
            blocker = QtCore.QSignalBlocker(control)
            control.setChecked(value)
            del blocker
        if state.get('preview'):
            image = QtGui.QPixmap()
            image.loadFromData(base64.b64decode(state['preview'].split(',', 1)[-1]))
            if not image.isNull():
                self.preview.image = image
                self.preview.update()
        reaction = state.get('reaction')
        self.cancel.setEnabled(bool(reaction))
        candidate = state.get('candidate')
        self.render_feedback()
        progress = state.get('progress', 0)
        self.progress.setVisible(bool(candidate and not reaction and progress > 0 and not state.get('needs_release')))
        self.progress.setValue(round(progress * 100))

    def render_feedback(self):
        state = self.last_state
        reaction = state.get('reaction')
        candidate = state.get('candidate')
        if self.action_error and time.monotonic() < self.error_until:
            text = self.text(self.action_error)
        elif not self.online:
            text = self.text('starting' if self.starting else 'off')
        elif state.get('error'):
            text = self.text(state.get('error_code') or state['error'])
        elif self.preview_error:
            text = self.text('preview_unavailable')
        elif reaction:
            text = self.text('reaction.' + reaction)
        elif not state.get('automatic', True):
            text = self.text('paused')
        elif state.get('needs_release'):
            text = self.text('release')
        elif state.get('cooldown', 0) > 0:
            text = self.text('cooldown')
        elif candidate:
            text = self.text('hold', reaction=self.text('reaction.' + candidate))
        else:
            text = self.text('ready')
        self.feedback.setText(text)

    def closeEvent(self, event):
        self.timer.stop()
        self.reader.close()
        self.executor.shutdown(wait=False, cancel_futures=True)
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('HandSpark')
    app.setDesktopFileName('handspark')
    name = f'teams-effects-panel-{os.getuid()}'
    client = QtNetwork.QLocalSocket()
    client.connectToServer(name)
    if client.waitForConnected(150):
        client.write(b'show')
        client.waitForBytesWritten(150)
        return
    QtNetwork.QLocalServer.removeServer(name)
    server = QtNetwork.QLocalServer()
    server.listen(name)
    panel = Panel()

    def show():
        connection = server.nextPendingConnection()
        if connection:
            connection.disconnectFromServer()
        panel.showNormal()
        panel.raise_()
        panel.activateWindow()

    server.newConnection.connect(show)
    panel.show()
    app.exec_()


if __name__ == '__main__':
    main()
