HandSpark 0.4.1 refines the app icon with two rounded arcs above the raised hand: a thin outer arc and a thicker inner arc.

The icon stays readable at small desktop and taskbar sizes. The golden thumbs-up animation introduced in 0.4.0 is included.

Camera output is configurable at 360p, 540p or 720p / 30 fps. Preview settings are independent and leave the meeting-camera device free for video apps. Existing language preferences are preserved. Autostart is disabled by default.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2 loopback driver remain system dependencies. See README.md for installation.
