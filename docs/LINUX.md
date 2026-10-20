# Linux camera setup

Ubuntu 24.04 amd64 / Python 3.12 / X11 is the tested target. The first webcam is
expected at `/dev/video0`, supporting 1280×720 MJPEG at 30 fps. To inspect devices:

```sh
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext
```

## Use a different physical camera

Create a systemd user override:

```sh
systemctl --user edit teams-effects.service
```

```ini
[Service]
Environment=HANDSPARK_CAMERA_DEVICE=/dev/video2
```

Then run `systemctl --user daemon-reload` and `systemctl --user restart teams-effects`.
A stable `/dev/v4l/by-id/...` path can also be used. Resolution and pixel-format
selection are currently fixed in `controller.configure`; arbitrary webcams
without 720p MJPEG need a source change.

## Persistent virtual camera

If you do not already have a loopback configuration, create:

`/etc/modules-load.d/handspark.conf`:

```text
v4l2loopback
```

`/etc/modprobe.d/handspark.conf`:

```text
options v4l2loopback video_nr=42 card_label="Teams Effects" exclusive_caps=1
```

Apply on reboot, or load the module with those options when it is not already
in use. Do not unload an active camera module during a call. Ensure device 42
is free; use another number if needed. OBS chooses an available loopback device.
If multiple virtual cameras exist, inspect OBS's virtual-camera output selection.

Some Ubuntu kernels already include a signed module. Use it instead of installing
an unnecessary DKMS copy. If using DKMS with Secure Boot, complete module signing
and MOK enrollment as directed by Ubuntu. The application never installs a kernel
module itself.

## OBS configuration

The panel reads the composed OBS scene through a dedicated JPEG stream, in
memory. It does not open the virtual-camera device, leaving the loopback
capture stream available for Teams, Zoom or another camera consumer. This also
works with drivers that permit only one capture stream. Preview resolution and
FPS remain independent of camera output; frames never exceed the configured
output resolution. The preview worker stops when its window closes; the
backend continues running.

Camera output defaults to 360p / 30 fps, with 540p and 720p available in the
panel. Output changes are applied to the stopped OBS profile before restarting
it, retaining the 720p scene coordinates for effects and masks. If you launched
OBS separately, close it before changing camera output.

First start creates the `Teams Effects` profile and collection under
`~/.config/obs-studio/` and enables authenticated OBS WebSocket on port 4467.
An existing OBS WebSocket configuration is backed up before the initial change.
Close OBS during this first setup. Subsequent starts use the dedicated profile;
an already running unrelated OBS profile is rejected.

Credentials live in `~/.config/teams-effects/obs-password` and
`~/.config/obs-studio/plugin_config/obs-websocket/config.json`, with private
permissions. They must not be committed to Git.
The application mutes OBS's special audio inputs in its dedicated profile;
Your video app continues using its own microphone selection.

The service starts only on demand. Closing the panel leaves video running;
`handspark stop` stops it. Native PyQt5 supplies the window, including your
desktop's fonts and palette. A matching SVG desktop/taskbar icon is installed.

## Cleanup

Stop HandSpark before removing its `.deb`. User data is retained by package removal.
For full cleanup, remove the following after checking whether you still need it:

- `~/.config/systemd/user/teams-effects.service` and its optional override folder.
- `~/.config/teams-effects/` and `~/.cache/teams-effects/`.
- The dedicated `Teams_Effects` OBS profile/collection, without deleting other profiles.
- Driver configuration you created specifically for HandSpark.

Reload user units with `systemctl --user daemon-reload`. If restoring the initial
OBS WebSocket backup, close OBS first and keep any later OBS changes you want.
