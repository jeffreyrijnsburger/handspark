"""Private, local control channel shared by the camera, panel and CLI."""
import json
import os
from pathlib import Path
import queue
import socket
import socketserver
import threading
import time
from reactions import REACTIONS
from i18n import translate
from settings import load_settings

RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'teams-effects'
SOCKET = RUNTIME / 'control.sock'


def request(command='status', **data):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(1.5)
        client.connect(str(SOCKET))
        client.sendall((json.dumps({'command': command, **data}) + '\n').encode())
        with client.makefile('rb') as stream:
            response = json.loads(stream.readline(2 * 1024 * 1024))
    if not response.get('ok'):
        message = response.get('error_code') or response.get('error', 'command_failed')
        raise RuntimeError(translate(load_settings()['language'], message))
    return response


class Control:
    def __init__(self):
        self.commands = queue.Queue(maxsize=64)
        self.lock = threading.Lock()
        self.state = {'ok': True, 'automatic': True, 'depth': True, 'reaction': None,
                      'candidate': None, 'progress': 0, 'hands': 0, 'cooldown': 0,
                      'needs_release': False,
                      'preview': None, 'error': None}
        self.preview_until = 0.0
        self.server = None

    def update(self, **values):
        with self.lock:
            self.state.update(values)

    def handle(self, data):
        command = data.get('command')
        if command == 'status':
            with self.lock:
                if data.get('preview'):
                    self.preview_until = time.monotonic() + 2
                result = dict(self.state)
                if not data.get('preview'):
                    result.pop('preview', None)
                return result
        if command not in ('react', 'automatic', 'depth', 'cancel'):
            return {'ok': False, 'error_code': 'unknown_command'}
        if command == 'react' and data.get('reaction') not in REACTIONS:
            return {'ok': False, 'error_code': 'unknown_reaction'}
        if command in ('automatic', 'depth') and type(data.get('enabled')) is not bool:
            return {'ok': False, 'error_code': 'boolean_required'}
        try:
            self.commands.put_nowait(data)
        except queue.Full:
            return {'ok': False, 'error_code': 'busy'}
        return {'ok': True}

    def start(self):
        owner = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                try:
                    self.connection.settimeout(2)
                    data = json.loads(self.rfile.readline(8192))
                    response = owner.handle(data)
                    self.wfile.write((json.dumps(response) + '\n').encode())
                except (OSError, ValueError):
                    pass

        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads = True

        RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
        SOCKET.unlink(missing_ok=True)
        self.server = Server(str(SOCKET), Handler)
        SOCKET.chmod(0o600)
        threading.Thread(target=self.server.serve_forever,
                         kwargs={'poll_interval': 0.1}, daemon=True).start()

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            SOCKET.unlink(missing_ok=True)
