#!/usr/bin/env python3
"""Capture the real panel using synthetic input and the actual encoded laser clip."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))


def capture_panel():
    from PyQt5 import QtGui, QtWidgets
    import panel
    import settings
    app = QtWidgets.QApplication([])
    app.setApplicationName('HandSpark')
    with tempfile.TemporaryDirectory() as directory:
        settings.SETTINGS_PATH = Path(directory) / 'settings.json'
        widget = panel.Panel(autostart=False, poll=False, manage_service=False)
        widget.resize(1100, 940)
        widget.apply_status({'automatic': True, 'depth': True, 'reaction': 'lasers',
                             'hands': 2, 'candidate': 'lasers'})
        widget.preview.image = QtGui.QPixmap(str(BASE / 'docs/demo-frame.png'))
        widget.show()
        app.processEvents()
        widget.grab().save(str(BASE / 'docs/handspark-demo.png'))
        widget.close()


def compose_frame():
    import cv2
    import mediapipe as mp
    import numpy as np
    from PIL import Image
    from gestures import classify
    from matte import soften_person
    from render_reactions import asset_signature
    manifest = json.loads((BASE / 'reactions-apple/render-manifest.json').read_text())
    if manifest.get('lasers') != asset_signature():
        raise RuntimeError('Render the latest lasers first: .venv/bin/python render_reactions.py lasers')
    photo = Image.open(BASE / 'docs/demo-person.png').convert('RGB').resize((960, 540), Image.Resampling.LANCZOS)
    rgb = np.asarray(photo)
    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(BASE / 'hand_landmarker.task')),
        num_hands=2, min_hand_detection_confidence=0.6, min_hand_presence_confidence=0.6)
    with mp.tasks.vision.HandLandmarker.create_from_options(options) as model:
        result = model.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.resize(rgb, (640, 360))))
        hands = [[(point.x, point.y) for point in hand] for hand in result.hand_landmarks]
    print('Generated input gesture:', classify([[(x * 16 / 9, y) for x, y in hand] for hand in hands]))
    options = mp.tasks.vision.ImageSegmenterOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(BASE / 'selfie_segmenter_landscape.tflite')),
        output_confidence_masks=True)
    with mp.tasks.vision.ImageSegmenter.create_from_options(options) as model:
        result = model.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.resize(rgb, (320, 180))))
        index = 0 if len(result.confidence_masks) == 1 else 1
        alpha = soften_person(result.confidence_masks[index].numpy_view().squeeze(), hands)
    encoded = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-ss', '2.2', '-i', str(BASE / 'reactions-apple/lasers.mov'),
        '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-threads', '1', '-'])
    lasers = Image.open(io.BytesIO(encoded)).convert('RGBA')
    camera = photo.convert('RGBA')
    foreground = camera.copy()
    mask = Image.fromarray((alpha * 255).astype(np.uint8)).resize(camera.size, Image.Resampling.BILINEAR)
    foreground.putalpha(mask)
    scene = Image.alpha_composite(Image.alpha_composite(camera, lasers), foreground)
    scene.save(BASE / 'docs/demo-frame.png')
    print('Demo uses the actual clip at 2.2 seconds and HandSpark person/hand masking.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-panel', action='store_true')
    args = parser.parse_args()
    if args.capture_panel:
        capture_panel()
    else:
        compose_frame()
        subprocess.run(['/usr/bin/python3', str(Path(__file__).resolve()), '--capture-panel'],
                       env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}, check=True)


if __name__ == '__main__':
    main()
