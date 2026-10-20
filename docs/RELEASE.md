HandSpark's first public release: a playful nod to Apple's Mac video reactions,
built independently for Linux webcams and Teams.

- Eight automatic gestures and manual controls, including two-handed metal-horns lasers.
- Soft person segmentation for effects behind your body.
- Native preview window, desktop/taskbar icon, pause and stop controls.
- Dutch/English configuration; Dutch is the default.
- Documented JSON CLI for scripts and AI agents.
- MIT-licensed original code and artwork.

Download the `.deb` and `SHA256SUMS` below. The package targets **Ubuntu 24.04
amd64 / Python 3.12 / X11** and includes Python inference packages, models and
rendered effects. It requires OBS 30.2+ (noble-backports), Qt/FFmpeg and a working
V4L2 loopback driver. Follow README.md's installation steps before first use.

Windows and macOS camera backends are not implemented. This is an initial 0.x
release; gesture detection and segmentation depend on lighting and hand visibility.
