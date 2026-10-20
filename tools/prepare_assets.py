#!/usr/bin/env python3
"""Download checksum-pinned MediaPipe models and render local reaction clips."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

BASE = Path(__file__).resolve().parent.parent


def prepare_models():
    for manifest, name in (('model.json', 'hand_landmarker.task'),
                           ('segmentation-model.json', 'selfie_segmenter_landscape.tflite')):
        spec = json.loads((BASE / manifest).read_text())
        target = BASE / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == spec['sha256']:
            continue
        print('Downloading ' + name, flush=True)
        with urllib.request.urlopen(spec['url'], timeout=60) as response:
            data = response.read(64 * 1024 * 1024 + 1)
        if len(data) > 64 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != spec['sha256']:
            raise RuntimeError('Model checksum mismatch: ' + name)
        temporary = target.with_suffix('.download')
        temporary.write_bytes(data)
        temporary.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models-only', action='store_true')
    args = parser.parse_args()
    prepare_models()
    if not args.models_only:
        sys.path.insert(0, str(BASE))
        from reactions import REACTIONS
        for reaction in REACTIONS:
            if not (BASE / 'reactions-apple' / (reaction + '.mov')).exists():
                subprocess.run([sys.executable, str(BASE / 'render_reactions.py'), reaction], check=True)


if __name__ == '__main__':
    main()
