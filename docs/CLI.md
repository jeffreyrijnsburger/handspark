# CLI contract, schema 1

`handspark --version` prints the application version. `handspark --help` lists
commands. `handspark commands --json` is the machine-readable discovery endpoint.
No network API or authentication token is needed to control the local app.

| Command | Behavior |
| --- | --- |
| `panel` (default) | Open/raise the native window and start the camera |
| `setup` | Configure the current user's dedicated OBS profile and service |
| `start` / `stop` | Start / stop the camera |
| `status` | Show systemd status and recent logs |
| `status --json` | Read current state, excluding any preview |
| `list [--json]` | List the eight IDs, localized names and gestures |
| `react ID` | Start the camera if needed and play a reaction |
| `ID` | Shorthand for `react ID` |
| `pause` / `resume` | Disable / enable automatic gestures, keeping video on |
| `cancel` | Clear all effects, keeping video on |
| `language [nl\|en] [--json]` | Read / save the UI language, even offline |
| `preview [--resolution 360\|540\|720] [--fps 15\|24\|30] [--json]` | Read / save preview resolution and frame rate, even offline |
| `commands --json` | Discover commands, languages and reaction IDs |

JSON is one UTF-8 object per invocation. Every JSON response contains
`schema_version: 1`, `version` and `ok`. Unknown additive fields should be ignored.
Reaction IDs are stable across languages:
`heart`, `balloons`, `thumbs_up`, `thumbs_down`, `rain`, `confetti`, `fireworks`, `lasers`.

An online status includes `automatic`, `depth`, `reaction` (ID or null),
`candidate`, `progress` (0–1), `hands`, `cooldown` (seconds), `needs_release`,
`remaining` (seconds), `mask_frames`, `error` and `error_code`.
No image, OBS password or user path is returned. A successful command exits 0.
Preview configuration JSON includes `preview_resolution` (height in pixels) and
`preview_fps`. Defaults are 360 and 30. These affect the panel's direct virtual
camera reader and never restart or reconfigure the meeting camera.
Invalid syntax exits 2; general operational failures exit 1.
An offline JSON status exits 3:

```json
{"schema_version":1,"version":"0.2.0","ok":false,"error_code":"camera_offline"}
```

`status`, `list`, `commands`, `--version` and reading `language` do not start a
camera or change settings. Reactions are accepted through a private local queue;
successful acceptance does not mean an effect has already finished. Poll status
to follow its lifetime. Pausing gestures and changing language do not interrupt
the video stream. Only `stop` shuts down the camera output.

The runtime socket lives at `$XDG_RUNTIME_DIR/teams-effects/control.sock`, mode
0600 inside a 0700 directory. Prefer the CLI over depending on the private IPC
format. Agents should use camera-changing commands within the user's request
and preserve the user's language preference.
