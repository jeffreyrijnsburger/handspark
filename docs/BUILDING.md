# Build and release

Use Ubuntu 24.04 amd64 with Python 3.12. Install OBS 30.2+ from noble-backports,
plus `python3-venv`, `python3-pyqt5`, `ffmpeg`, `v4l-utils`, `libgl1`,
`libportaudio2`, `dpkg-dev` and `git` through apt.

## Run from source

```sh
git clone https://github.com/jeffreyrijnsburger/handspark.git
cd handspark
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python tools/prepare_assets.py
chmod +x bin/handspark
bin/handspark setup
bin/handspark panel
```

Set up V4L2 loopback as described in the README before starting the camera.
The source checkout must stay at its installed location because the generated
user unit points to it. The `.deb` uses `/opt/handspark` instead.
If moving the checkout, run `bin/handspark setup` again.

The model manifests pin SHA-256 values. A changed or unavailable upstream model
causes setup to fail instead of silently using a different model. Animation clips
are generated locally using Pillow/NumPy and FFmpeg's lossless QTRLE codec.
Generated models, clips, venvs and user data are excluded from Git.

## Tests

Prepare the pinned models to include the real ONNX smoke test.

```sh
.venv/bin/python tools/prepare_assets.py --models-only
.venv/bin/python -m unittest test_gestures test_controls test_i18n test_bootstrap test_cli test_lasers test_reactions test_preview_stream test_hagrid test_lifecycle -v
QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest test_panel test_preview -v
```

Unit tests cover HaGRID preprocessing, confidence handling, fallback and model integrity,
gesture geometry, two-hand priority, duplicate rejection,
hold/release/cooldown, mask edges, private control IPC, language persistence,
concurrent settings updates, fresh OBS bootstrap, CLI JSON and live UI translation.
Hardware validation also needs a physical webcam, loopback device and OBS.

## Build a package

```sh
python3 tools/build_deb.py
dpkg-deb --info dist/handspark_0.6.1_ubuntu24.04_amd64.deb
(cd dist && sha256sum -c SHA256SUMS)
```

To check the manifest, run `(cd dist && sha256sum -c SHA256SUMS)`.
The build verifies the runtime against `requirements.lock`, prepares assets and
bundles Python packages with their distribution licenses. System Python 3.12,
PyQt5, OBS and FFmpeg are apt dependencies. No root install scripts or pip/network
operations run during apt installation. The app configures user files on first launch.

`--runtime /path/to/venv` can reuse an already installed matching Python 3.12
environment. Python dependency versions are pinned; this does not claim
bit-for-bit reproducibility across different build machines or future apt mirrors.

## Publish a version

1. Update `VERSION` and `CHANGELOG.md`; follow SemVer with `0.x.y` while experimental.
2. Run tests and validate the package. Open a feature-branch pull request with a semantic title, wait for the required `test` check, and squash-merge into protected main.
3. Create an annotated `v0.x.y` tag matching `VERSION`.
4. The release workflow builds/tests on Ubuntu 24.04, creates the GitHub Release
   and attaches the `.deb` and `SHA256SUMS`. GitHub supplies source archives.
5. Check the release assets and installation instructions before announcing it.

The first release is `v0.1.0`. Releases are downloadable at
https://github.com/jeffreyrijnsburger/handspark/releases/latest
