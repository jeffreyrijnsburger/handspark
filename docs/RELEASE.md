HandSpark 0.7.0 starts in the system tray by default, with a saved option to show the window instead.

- Enable or disable **Start in system tray** in the Dutch/English controls.
- Use the tray icon to open the controls, or launch HandSpark again to raise
  an existing instance. Hidden controls do not run a preview worker.
- Fall back to a visible window if the tray is disabled or unavailable.
  Camera startup errors also open the controls so they can be resolved.
- Configure startup offline with `handspark on-start tray|window`, with JSON
  available for automation. Disabling the tray restores visible-window startup.
- Preserve existing camera output, language and close-button preferences.

Starting in the tray affects window visibility. Camera startup still follows
an explicit application launch; OS login autostart remains opt-in for new installs.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference
dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2
loopback driver remain system dependencies. See README.md for installation.
