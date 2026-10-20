HandSpark 0.6.1 fixes the missing system tray icon on KDE/StatusNotifier desktops.

The tray now supplies concrete image sizes from the existing vector logo,
including small and high-density variants. This preserves the mint hand and
two gold arcs and avoids an empty or generic system tray icon.

Configurable closing, tray controls, camera behavior and saved language settings
are unchanged. Autostart remains disabled by default for new installations.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference
dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2
loopback driver remain system dependencies. See README.md for installation.
