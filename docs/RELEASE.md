HandSpark 0.5.0 adds a small local HaGRID image classifier for more natural thumbs up/down.

- Combine image evidence with MediaPipe geometry for thumbs up/down, fireworks and rain.
- Use basic finger/direction checks, geometric fallback for uncertain predictions and the existing hold/release/cooldown behavior.
- Keep recovered thumbs’ animation placement and duplicate-hand protection.
- Run with the existing OpenCV dependency; the model is about 0.4 MB and bundled with its upstream license and checksum-pinned provenance.
- Preserve geometric recognition if the model is missing, invalid or fails inference. The additive `gesture_engine` status field identifies the active recognizer.

Two small public HaGRID development checks covered 360 images. Among hands with usable tracking, the combined recognizer found 32 of 36 thumb examples versus 26 using geometry alone, with zero thumb reactions on 336 non-thumb hands. This is a sanity check, not an independent accuracy benchmark: upstream training overlap is unknown, and live video recognition remains dependent on tracking and camera conditions. See docs/HAGRID.md for the protocol and limits.

Existing language preferences and camera output settings are preserved. Autostart is disabled by default.

The `.deb` targets Ubuntu 24.04 amd64 / Python 3.12 / X11 and bundles inference dependencies, models and effects. OBS 30.2+, Qt/FFmpeg and a working V4L2 loopback driver remain system dependencies. See README.md for installation.
