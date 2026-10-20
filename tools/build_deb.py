#!/usr/bin/env python3
"""Build the Ubuntu 24.04 amd64 package with models, clips and Python dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=BASE / '.venv', help='Python 3.12 venv installed from requirements.lock')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12) or platform.machine() != 'x86_64':
        parser.error('Build on Ubuntu 24.04 amd64 with Python 3.12')
    runtime = args.runtime.resolve()
    python = runtime / 'bin/python'
    subprocess.run([str(python), str(BASE / 'tools/prepare_assets.py')], check=True)
    expected = {line.strip().lower() for line in (BASE / 'requirements.lock').read_text().splitlines() if line.strip()}
    code = ('import importlib.metadata as m; '
            'print("\\n".join(d.metadata["Name"]+"=="+d.version for d in m.distributions() '
            'if d.metadata["Name"].lower() not in ("pip", "setuptools", "wheel")))')
    installed = set(subprocess.check_output([str(python), '-c', code], text=True).lower().splitlines())
    if expected != installed:
        raise RuntimeError('Runtime does not match requirements.lock: ' + ', '.join(sorted(expected ^ installed)))
    version = (BASE / 'VERSION').read_text().strip()
    output = BASE / 'dist'
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='handspark-build-') as directory:
        stage = Path(directory)
        app = stage / 'opt/handspark'
        app.mkdir(parents=True)
        for pattern in ('*.py', '*.json', 'requirements.lock', 'VERSION', 'LICENSE', 'THIRD_PARTY_NOTICES.md', '*.task', '*.tflite', '*.onnx'):
            for source in BASE.glob(pattern):
                if not source.name.startswith('test_'):
                    shutil.copy2(source, app / source.name)
        for name in ('bin', 'icons', 'emoji', 'reactions-apple', 'licenses'):
            shutil.copytree(BASE / name, app / name, ignore=shutil.ignore_patterns('__pycache__'))
        library = app / '.venv/lib/python3.12/site-packages'
        shutil.copytree(runtime / 'lib/python3.12/site-packages', library,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'pip', 'pip-*.dist-info'))
        interpreter = app / '.venv/bin'
        interpreter.mkdir(parents=True)
        (interpreter / 'python').symlink_to('/usr/bin/python3')
        (app / '.venv/pyvenv.cfg').write_text('home = /usr/bin\ninclude-system-site-packages = false\nversion = 3.12\n')
        bindir = stage / 'usr/bin'
        bindir.mkdir(parents=True)
        (bindir / 'handspark').symlink_to('/opt/handspark/bin/handspark')
        os.chmod(app / 'bin/handspark', 0o755)
        for source, destination in (
            (BASE / 'packaging/handspark.desktop', stage / 'usr/share/applications/handspark.desktop'),
            (BASE / 'icons/handspark.svg', stage / 'usr/share/icons/hicolor/scalable/apps/handspark.svg'),
            (BASE / 'LICENSE', stage / 'usr/share/doc/handspark/copyright'),
            (BASE / 'README.md', stage / 'usr/share/doc/handspark/README.md')):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        info = {'version': version, 'target': 'ubuntu-24.04-amd64',
                'requirements_sha256': hashlib.sha256((BASE / 'requirements.lock').read_bytes()).hexdigest()}
        (app / 'BUILD-INFO.json').write_text(json.dumps(info, indent=2) + '\n')
        control = stage / 'DEBIAN'
        control.mkdir()
        size = sum(p.stat().st_size for p in stage.rglob('*') if p.is_file() and not p.is_symlink()) // 1024
        (control / 'control').write_text(f'''Package: handspark
Version: {version}
Architecture: amd64
Maintainer: Jeffrey Rijnsburger <jeffreyrijnsburger@users.noreply.github.com>
Section: video
Priority: optional
Installed-Size: {size}
Depends: python3 (>= 3.12), python3 (<< 3.13), python3-pyqt5, obs-studio (>= 30.2), ffmpeg, v4l-utils, libgl1, libglib2.0-0t64, libportaudio2, procps
Suggests: v4l2loopback-dkms
Homepage: https://github.com/jeffreyrijnsburger/handspark
Description: Local hand gesture reactions for Linux video calls
 Native controls, eight gesture reactions and OBS virtual camera integration.
 Includes the inference runtime, models and rendered animations.
''')
        target = output / f'handspark_{version}_ubuntu24.04_amd64.deb'
        subprocess.run(['dpkg-deb', '--root-owner-group', '--threads-max=2', '-Zzstd', '-z10', '--build', str(stage), str(target)], check=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(f'{digest}  {target.name}\n')
    print(target)


if __name__ == '__main__':
    main()
