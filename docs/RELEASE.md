HandSpark 0.3.0 adds lighter camera output and improves reactions.

- The composed preview leaves the virtual-camera capture stream available for meeting clients, including loopback drivers with exclusive capture.
- Camera output defaults to 360p / 30 fps. Choose 360p, 540p or 720p in the native panel, independently of preview resolution. Changing output briefly restarts the camera.
- `handspark output --resolution 360` saves output size offline; `handspark restart` explicitly applies it. Online status reports the output size and frame rate from OBS.
- Thumbs up/down use glass bubbles, shaded silver fingers and a soft pop animation.
- A softly lit volumetric storm cloud and its shadow stay fully inside the video. Layered rainfall and two branching lightning strikes emerge beneath it, with brief illumination inside the cloud. All rendering happens during asset preparation.
- Stricter geometry requires a straight, extended thumb beyond folded fingers to reduce accidental thumb reactions, rain and fireworks.

The interface now uses app-neutral labels, with camera selection guidance for Teams and Zoom in the README.

Existing language preferences are preserved; new installations default to English. Autostart remains disabled by default.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2 loopback driver remain system dependencies. See README.md for installation. Camera output is validated locally; actual Teams call latency has not been measured.
