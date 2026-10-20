HandSpark 0.4.2 makes the camera controls clearer.

- Use “Turn camera on/off” in English and “Camera inschakelen/uitschakelen” in Dutch, including the desktop action.
- Explain that turning the camera off stops HandSpark’s camera feed, virtual camera and reactions for your video app.
- Keep button tooltips synchronized with camera state and language, and clarify that closing the window leaves the camera running outside calls.

The camera controls behave as before. Existing language preferences are preserved. Autostart is disabled by default.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2 loopback driver remain system dependencies. See README.md for installation.
