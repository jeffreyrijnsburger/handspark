HandSpark 0.4.3 improves natural thumbs-up and thumbs-down recognition.

- Accept shorter thumb extension, modest hand tilt and a relaxed fist.
- Measure extension along the thumb and allow folded fingers more tolerance in oblique views.
- Apply the same improvement to two thumbs up (fireworks) and two thumbs down (rain).
- Retain upright-direction, thumb-joint and finger-separation checks, along with the existing hold and cooldown behavior.

Regression tests cover compact and relaxed poses across mirroring, tilt and scale, small tracking jitter, outstretched fingers and existing rejection cases. Gesture validation for this release uses synthetic landmarks.

Existing language preferences are preserved. Autostart is disabled by default.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2 loopback driver remain system dependencies. See README.md for installation.
