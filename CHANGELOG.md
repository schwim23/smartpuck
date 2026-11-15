# Changelog

One plain-English line per merged change. New lines go under **Unreleased**; on tagging, move them under the version.

## Unreleased

- Hold to talk: press and hold the screen ~0.6 s to talk without the wake word (the wake word model misses kids' voices).
- Wake word sensitivity setting in HA (Default / Moderately / Very sensitive).

- Nightly backup of Home Assistant state and all secrets (`scripts/backup.sh`, cron 3:15 AM, 14 days, verified). Restore tested.

- Added `scripts/pr.py` to open, check and squash-merge pull requests from the command line.

- Reserved the puck's address (192.168.1.221) on the Fios router so OTA and HA links survive reboots.

- Turned off the ESPHome dashboard's version history so it stops creating a nested git repo in `esphome/`.

## puck-v0.1.0 (2026-11-14)

- First flash of the V2 board: Waveshare display init, V2 audio (shared I2S, ES8311/ES7210, amp on GPIO15).
- Clock with SNTP fallback, weather and hourly forecast ring from `weather.home`.
- Music page on Kitchen Sonos; Living/Dining auto-grouped; play/pause and grouped volume.
- Voice: "Hey Jarvis" wake word, Whisper speech-to-text, Piper text-to-speech (assistant "Puck").
- Thermostat page skipped until a climate entity exists.
- Repo created: README, CLAUDE.md, test script, secret and docs hooks.
