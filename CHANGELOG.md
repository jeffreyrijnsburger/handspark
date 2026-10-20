# Changelog

## 0.2.0 — 2026-10-20

- Replace the roughly 2-fps screenshot preview with a live feed of the actual
  virtual camera, independent of status polling and gesture processing.
- Select 360p, 540p or 720p preview resolution and 15, 24 or 30 fps in the panel.
  Default to 360p/30 fps and save the selection across launches.
- Add offline CLI preview configuration for humans and agents.
- Drop stale preview frames and stop the reader when the window/camera closes.
- Preserve the saved language and the camera output used by meeting clients.

## 0.1.1 — 2026-10-20

- Default new installations to English while preserving existing saved languages.
- Upgrade lasers to a concert stage: sixteen sweeping neon beams, volumetric
  light, projector flares, rotating 3D light ribbons, depth streaks, expanding
  rings, floating haze and a moving perspective floor.
- Preserve vivid colors at soft glow edges in transparent video.
- Invalidate cached animations when their rendering source changes.
- Add a synthetic animated laser preview and regression coverage.
- Protect main with pull requests and a required GitHub Actions test check;
  disallow force pushes/deletion and enforce the same rules for admins.

## 0.1.0 — 2026-10-20

First public Linux release.

- Eight gesture reactions: hearts, balloons, thumbs up/down, rain, confetti,
  fireworks and two-handed metal-horns lasers.
- OBS virtual camera output for Teams and other video applications.
- Soft person segmentation places background reactions behind the person.
- Native Qt controls with a live preview, manual reactions, pause and cancel.
- Persistent Dutch and English UI; Dutch is the default.
- HandSpark SVG logo and desktop/taskbar icon.
- Local CLI with versioned JSON responses for agents and automation.
- Ubuntu 24.04 amd64 `.deb`, bundled inference dependencies and assets,
  release checksums, tests and build instructions.

Versions follow SemVer. While below 1.0, minor releases may change public
interfaces; patch releases preserve the current CLI schema.
