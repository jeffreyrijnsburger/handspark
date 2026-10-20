# Contributing

Humans and AI agents are welcome. Contributions use the project's MIT license;
keep third-party notices and licenses intact. Start with `README.md`,
`docs/BUILDING.md` and `AGENTS.md`.

For a bug, include the HandSpark version, OS, desktop session (X11/Wayland),
OBS version, camera model, expected behavior and steps to reproduce. Small,
focused pull requests are easier to review. Explain the visible behavior change
and how you tested it. Do not attach private credentials or camera recordings.

Use a feature branch and a semantic English commit/PR title, for example
`fix(gestures): tolerate brief tracking gaps`. Main is protected, including for
admins. Pull requests require the `test` check, resolved conversations and an
up-to-date branch; squash merging keeps history linear. No second human approval
is required for this small project. Never bypass protection or force-push main.

Translate user-facing text in both `en` and `nl`. English is the fresh-install
default; preserve a user's saved language. Keep reaction IDs and OBS source names
stable. Use the shared settings merger and private local control channel.

Run the relevant tests and checks in `docs/BUILDING.md`. Use synthetic frames
for public demos. Document platform limits honestly; the current tested target
is Ubuntu 24.04 amd64/X11. For a new platform backend, describe how its virtual
camera and process lifecycle will work before introducing a large rewrite.

Report security issues privately using `SECURITY.md`. For ordinary questions,
use repository issues. This is a community project without a guaranteed response time.
