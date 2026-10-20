#!/usr/bin/env python3
"""Download checksum-pinned recognition models and render local reaction clips."""
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
                           ('segmentation-model.json', 'selfie_segmenter_landscape.tflite'),
                           ('hagrid-model.json', 'hagrid_crops.onnx')):
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
        from reactions import ALL_REACTIONS
        from render_reactions import asset_signature
        try:
            signatures = json.loads((BASE / 'reactions-apple/render-manifest.json').read_text())
        except (OSError, ValueError):
            signatures = {}
        signature = asset_signature()
        for reaction in ALL_REACTIONS:
            if (not (BASE / 'reactions-apple' / (reaction + '.mov')).exists()
                    or signatures.get(reaction) != signature):
                subprocess.run([sys.executable, str(BASE / 'render_reactions.py'), reaction], check=True)


if __name__ == '__main__':
    main()
