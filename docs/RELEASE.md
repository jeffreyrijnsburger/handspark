HandSpark 0.6.0 adds a configurable system tray and reliable camera shutdown.

- Show an optional tray icon with Open HandSpark, camera on/off and Quit.
- Choose what × does: stop camera and owned OBS (default), keep video running
  in the background, or hide the window in the tray. Preferences are saved.
- Configure the same behavior offline with `handspark on-close stop|background|tray`
  and `handspark tray on|off`, including JSON for automation.
- Pause hidden previews and restore the window if its tray becomes unavailable.
  Tray Quit always stops the camera and the OBS started by HandSpark.
- Shut down video before OBS, handle lost connections, cancel in-flight starts
  before stopping, and keep the window responsive with retry after errors.
- Leave an independently started OBS open. An OBS exit/failure no longer
  automatically reopens the camera; turn it on again explicitly when ready.

Existing language preferences and camera output settings are preserved.
Autostart is disabled by default.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference
dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2
loopback driver remain system dependencies. See README.md for installation.
