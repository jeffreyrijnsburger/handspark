HandSpark 0.2.1 improves gesture precision and the rain effect.

- Thumbs up/down require a straight, fully extended thumb that clearly projects beyond folded fingers, reducing accidental reactions. The same checks apply to fireworks and rain.
- Deliberate tilted and mirrored thumb gestures are covered by regression tests.
- The rain cloud and shadow have transparent padding and stay fully inside the video.
- Rounded cloud shading, gentle cloud movement and layered rainfall replace the clipped cloud. Drops emerge beneath the cloud.

The configurable live preview from 0.2.0 remains: 360p, 540p or 720p at 15, 24 or 30 fps. Default: 360p / 30 fps. Existing language preferences are preserved; new installations default to English.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2 loopback driver remain system dependencies. See README.md for installation. An actual Teams call is not part of this validation.
