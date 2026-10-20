# Third-party notices

HandSpark's original source, SVG icons, logo and animation renderer use the MIT
license in `LICENSE`. Dependencies and third-party artwork keep their own licenses.

## Noto Emoji artwork

`emoji/emoji_u1f44d.png`, `emoji_u1f44e.png` and `emoji_u1f496.png` are Google Noto
Emoji artwork. Copyright Google, Inc. Licensed under Apache-2.0; the complete
license is in `emoji/LICENSE`. The thumb images also appear in rendered reaction
clips. Source: https://github.com/googlefonts/noto-emoji

## MediaPipe models and runtime

MediaPipe is developed by Google and licensed under Apache-2.0. The model URLs
and exact SHA-256 values are recorded in `model.json` and
`segmentation-model.json`. The MediaPipe license is included in
`licenses/mediapipe-APACHE-2.0.txt`.

https://github.com/google-ai-edge/mediapipe
https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter

## Packaged Python dependencies

The `.deb` includes the packages pinned in `requirements.lock`. Their original
distribution metadata, copyright notices and license files remain alongside
them under `/opt/handspark/.venv/lib/python3.12/site-packages/`.
They include MediaPipe, NumPy, OpenCV, Pillow, matplotlib and websocket-client.
These packages are not relicensed by HandSpark's MIT license.

## System dependencies

OBS Studio, FFmpeg, PyQt5/Qt and v4l2loopback are separate system dependencies.
They are installed and licensed by the operating system; the `.deb` does not
bundle their executables. In particular, PyQt5 and OBS have GPL licensing terms.

## Reactions

Gesture-to-effect mappings are inspired by Apple's documented video reactions:
https://support.apple.com/en-us/105117
The animations are rendered from HandSpark's own source. No Apple animation,
3D engine, framework, logo or other proprietary artwork is included.
HandSpark is independent of Apple, Microsoft and OBS.
