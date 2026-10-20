HandSpark 0.2.0 replaces the slow snapshot preview with live video.

- The old preview refreshed at roughly 2 fps; the new reader displays the actual virtual camera independently of status polling.
- Choose 360p, 540p or 720p and 15, 24 or 30 fps in the native panel. Default: 360p / 30 fps.
- Settings are saved, work offline, and are available through `handspark preview --json`.
- Stale frames are dropped to keep latency low; closing the window stops its reader and leaves the camera service running.
- Existing language preferences are preserved. English is the default for new users.

Local measurements: 30 fps at 360p during lasers, 24 fps at 720p, and 15 fps at 360p. Both decoded frames and Qt preview paints were measured. An actual Teams call is not part of this validation.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2 loopback driver remain system dependencies. See README.md for installation.
