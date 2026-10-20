"""Shared preferences; merge changes so camera controls preserve the UI language."""
import fcntl
import json
import os
from pathlib import Path
import tempfile

SETTINGS_PATH = Path.home() / '.config/teams-effects/settings.json'
DEFAULTS = {'automatic': True, 'depth': True, 'language': 'nl'}
LANGUAGES = {'nl': 'Nederlands', 'en': 'English'}


def load_settings():
    try:
        saved = json.loads(SETTINGS_PATH.read_text())
    except (OSError, ValueError):
        saved = {}
    if not isinstance(saved, dict):
        saved = {}
    values = {**DEFAULTS, **saved}
    for key in ('automatic', 'depth'):
        if type(values[key]) is not bool:
            values[key] = DEFAULTS[key]
    if not isinstance(values['language'], str) or values['language'] not in LANGUAGES:
        values['language'] = DEFAULTS['language']
    return values


def update_settings(**updates):
    for key, value in updates.items():
        if key not in DEFAULTS:
            raise ValueError(f'Unknown setting: {key}')
        if key == 'language':
            if not isinstance(value, str) or value not in LANGUAGES:
                raise ValueError('Supported languages: nl, en')
        elif type(value) is not bool:
            raise ValueError(f'{key} must be a boolean')
    SETTINGS_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(SETTINGS_PATH.with_suffix('.lock'), os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(descriptor, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        values = {**load_settings(), **updates}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=SETTINGS_PATH.parent,
                                             prefix='settings-', suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(json.dumps(values, indent=2) + '\n')
            temporary.replace(SETTINGS_PATH)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
    return values
