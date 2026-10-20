# HandSpark for agents

HandSpark is an MIT-licensed Linux application for local webcam reactions.
Humans and AI agents may use, modify and redistribute it under `LICENSE`.

## Discover and use

Read `README.md`, `docs/CLI.md` and `VERSION`. Start with:

```sh
handspark --version
handspark commands --json
handspark list --json
handspark status --json
```

The CLI is the supported automation interface. JSON responses contain
`schema_version: 1` and `version`; reaction IDs are language-independent.
Read commands do not start a camera.
`output --resolution 360` saves camera output size without restarting; apply with
`restart` when authorized. The panel output selector restarts immediately.
Default output is 360p / 30 fps; preview settings are independent. `status --json` never returns an image.
An offline camera returns JSON with `ok: false`, `error_code: camera_offline`
and exit code 3.

`handspark react lasers` starts the webcam if needed and triggers a reaction.
Use camera-changing commands within the human's requested task. `cancel`
stops an effect; `stop` stops the camera. Closing the panel leaves video on.
Do not change an existing user's saved language unless asked. English is the
default; Dutch is supported with `handspark language nl`.

## Development

Python 3.12; Ubuntu 24.04 amd64/X11 is the tested target. Windows and macOS
camera backends are not implemented. Use a venv from `requirements.lock`.

```sh
.venv/bin/python tools/prepare_assets.py --models-only
.venv/bin/python -m unittest test_gestures test_controls test_i18n test_bootstrap test_cli test_lasers test_reactions test_preview_stream test_hagrid -v
QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest test_panel test_preview -v
```

Keep OBS source names stable. Translate UI strings through `i18n.py`.
Merge settings through `settings.update_settings` so concurrent camera and
language changes cannot overwrite each other. Never commit OBS credentials,
settings, camera images, generated clips, model binaries or a Python venv.
Models must match manifest checksums; clips are built from source.
Prepare models with `.venv/bin/python tools/prepare_assets.py --models-only`
for the real-model smoke test. The HaGRID model is a separately licensed asset;
keep its provenance and license. `gesture_engine` reports image classification
or geometric fallback; see `docs/HAGRID.md`.

Version changes update `VERSION` and `CHANGELOG.md`; release tags are `v0.x.y`.
Use semantic commits: `feat(scope): subject`, `fix(scope): subject`, etc.
Run relevant tests before publishing. See `docs/BUILDING.md` for release builds.
Main is protected, including for admins. Use a feature branch and pull request,
wait for the `test` check, and squash-merge. Do not bypass protection or force-push.
