"""Set up this user's dedicated OBS profile and camera service, without root."""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile


def private_write(path, text):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        temporary.replace(path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def configure_obs():
    home = Path.home()
    password_path = home / '.config/teams-effects/obs-password'
    config_path = home / '.config/obs-studio/plugin_config/obs-websocket/config.json'
    try:
        current = json.loads(config_path.read_text())
    except (OSError, ValueError):
        current = {}
    if not isinstance(current, dict):
        current = {}
    password = password_path.read_text().strip() if password_path.exists() else None
    ready = (password and current.get('server_password') == password
             and current.get('server_enabled') is True
             and current.get('auth_required') is True
             and current.get('server_port') == 4467)
    if not ready:
        if subprocess.run(['pgrep', '-x', 'obs'], stdout=subprocess.DEVNULL).returncode == 0:
            raise RuntimeError('Close OBS before the first HandSpark setup / Sluit OBS voor de eerste installatie.')
        if config_path.exists():
            backup = config_path.with_suffix('.json.before-handspark')
            if not backup.exists():
                shutil.copy2(config_path, backup)
                backup.chmod(0o600)
        password = password or secrets.token_urlsafe(32)
        private_write(password_path, password + '\n')
        current.update(server_enabled=True, server_port=4467, auth_required=True,
                       server_password=password, first_load=False, alerts_enabled=False)
        private_write(config_path, json.dumps(current, indent=2) + '\n')
    profile = home / '.config/obs-studio/basic/profiles/Teams_Effects/basic.ini'
    if not profile.exists():
        private_write(profile, '[General]\nName=Teams Effects\n\n[Video]\nBaseCX=1280\nBaseCY=720\n'
                      'OutputCX=1280\nOutputCY=720\nFPSType=0\nFPSCommon=30\n\n'
                      '[Audio]\nSampleRate=48000\nChannelSetup=Stereo\n')
    collection = home / '.config/obs-studio/basic/scenes/Teams_Effects.json'
    if not collection.exists():
        private_write(collection, json.dumps({
            'name': 'Teams Effects', 'current_scene': 'Teams Effects',
            'current_program_scene': 'Teams Effects',
            'sources': [{'name': 'Teams Effects', 'id': 'scene', 'versioned_id': 'scene',
                         'settings': {'items': []}}],
            'scene_order': [{'name': 'Teams Effects'}], 'groups': [], 'transitions': [],
            'current_transition': 'Fade', 'transition_duration': 300,
            'virtual-camera': {'type2': 3}, 'resolution': {'x': 1280, 'y': 720}}, indent=2) + '\n')


def unit_text(base):
    # systemd specifiers and quoting are distinct from shell escaping.
    quoted = str(base).replace('%', '%%').replace('\\', '\\\\').replace('"', '\\"')
    return f'''[Unit]
Description=HandSpark camera reactions
After=graphical-session.target
PartOf=graphical-session.target
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=notify
ExecStart="{quoted}/.venv/bin/python" "{quoted}/controller.py"
WorkingDirectory="{quoted}"
TimeoutStopSec=15
TimeoutStartSec=60
Environment=PYTHONUNBUFFERED=1
Restart=on-failure
RestartSec=2
'''


def ensure_setup(base):
    if not (base / '.venv/bin/python').exists():
        raise RuntimeError('Install the Python runtime first; see README.md / Installeer eerst de Python-omgeving.')
    configure_obs()
    unit = Path.home() / '.config/systemd/user/teams-effects.service'
    text = unit_text(base)
    if not unit.exists() or unit.read_text() != text:
        private_write(unit, text)
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
