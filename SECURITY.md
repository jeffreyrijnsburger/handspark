# Security reports

Please report vulnerabilities privately through GitHub's security reporting:
https://github.com/jeffreyrijnsburger/handspark/security/advisories/new

Include the affected version, reproduction steps and impact, using synthetic
data where possible. Do not post OBS passwords, tokens or real camera recordings
in public issues. The latest 0.x release is the maintenance target; this small
community project does not promise a response deadline.

HandSpark uses local inference, an authenticated local OBS connection and a
user-only Unix socket. Its normal status CLI omits preview images. Those are
intended boundaries; reports of a way around them are welcome.
