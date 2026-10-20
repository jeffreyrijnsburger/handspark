# CLI contract, schema 1

`handspark --version` prints the application version. `handspark --help` lists
commands. `handspark commands --json` is the machine-readable discovery endpoint.
No network API or authentication token is needed to control the local app.

| Command | Behavior |
| --- | --- |
| `panel` (default) | Open/raise the native window and start the camera |
| `setup` | Configure the current user's dedicated OBS profile and service |
| `start` / `stop` | Start / stop the camera |
| `restart` | Restart the camera and apply saved output resolution |
| `status` | Show systemd status and recent logs |
| `status --json` | Read current state, excluding any preview |
| `list [--json]` | List the eight IDs, localized names and gestures |
| `react ID` | Start the camera if needed and play a reaction |
| `ID` | Shorthand for `react ID` |
| `pause` / `resume` | Disable / enable automatic gestures, keeping video on |
| `cancel` | Clear all effects, keeping video on |
| `language [nl\|en] [--json]` | Read / save the UI language, even offline |
| `preview [--resolution 360\|540\|720] [--fps 15\|24\|30] [--json]` | Read / save preview resolution and frame rate, even offline |
| `output [--resolution 360\|540\|720] [--json]` | Read / save camera output size; applies on next start/restart, fixed 30 fps |
| `on-close [stop\|background\|tray] [--json]` | Read / save what × does; default `stop`; `tray` also enables the icon |
| `tray [on\|off] [--json]` | Read / save tray visibility; disabling it resets `tray` close action to `stop` |
| `commands --json` | Discover commands, languages and reaction IDs |

JSON is one UTF-8 object per invocation. Every JSON response contains
`schema_version: 1`, `version` and `ok`. Unknown additive fields should be ignored.
Reaction IDs are stable across languages:
`heart`, `balloons`, `thumbs_up`, `thumbs_down`, `rain`, `confetti`, `fireworks`, `lasers`.

An online status includes `automatic`, `depth`, `reaction` (ID or null),
`candidate`, `progress` (0–1), `hands`, `cooldown` (seconds), `needs_release`,
`remaining` (seconds), `mask_frames`, `gesture_engine`, `error` and `error_code`.
`gesture_engine` is `hagrid+geometry` when the image classifier is available,
or `geometry` when it falls back. This does not change the reaction IDs.
No image, OBS password or user path is returned. A successful command exits 0.
Preview configuration JSON includes `preview_resolution` (height in pixels) and
`preview_fps`. Defaults are 360 and 30. These affect the panel's independent composed-preview
feed and never restart or reconfigure the meeting camera.
`output --json` returns saved `output_resolution`, fixed `output_fps: 30` and
`applies_on_next_start: true`. Saving does not start or restart a camera; use
`restart` explicitly when ready. Default output is 360p. Online status includes
actual `output_resolution` and `output_fps` reported by OBS. The panel's output
selector saves and restarts an already running camera automatically.
`on-close --json` and `tray --json` include `close_action` and `tray_enabled`.
Reading or saving these settings does not start/stop a camera. An open panel
applies changes automatically. `stop` closes video and owned OBS on ×;
`background` exits the panel while video stays on; `tray` hides the panel while
video stays on. Without a tray, `tray` falls back to stopping. The tray's Quit
action always stops video and owned OBS. Independently started OBS stays open.
Invalid syntax exits 2; general operational failures exit 1.
An offline JSON status exits 3:

```json
{"schema_version":1,"version":"0.6.0","ok":false,"error_code":"camera_offline"}
```

`status`, `list`, `commands`, `--version` and reading `language`, `preview` or
`output`, `on-close` or `tray` do not start a
camera or change settings. Reactions are accepted through a private local queue;
successful acceptance does not mean an effect has already finished. Poll status
to follow its lifetime. Pausing gestures and changing language do not interrupt
the video stream. `stop` shuts down the camera output; `restart` interrupts it
briefly while applying saved output settings.

The runtime socket lives at `$XDG_RUNTIME_DIR/teams-effects/control.sock`, mode
0600 inside a 0700 directory. Prefer the CLI over depending on the private IPC
format. Agents should use camera-changing commands within the user's request
and preserve the user's language preference.
