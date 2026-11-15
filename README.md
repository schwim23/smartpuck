# Smart Puck

A kitchen smart display and voice assistant: a Waveshare ESP32-S3-Touch-LCD-1.85C **V2** running ESPHome, backed by Home Assistant, Whisper and Piper in Docker on the Ubuntu host `prometheus`.

What it does today:

- Clock face with weather and an hourly forecast ring
- Music page for the Kitchen Sonos (Living/Dining auto-grouped), with play/pause and grouped volume
- Voice assistant: "Hey Jarvis" or "Okay Nabu", local speech-to-text (Whisper) and text-to-speech (Piper). A **Wake word sensitivity** setting on the puck's HA device page (Default / Moderately / Very sensitive) changes how readily it wakes, with no reflash

Last updated: 2026-11-14 · Current firmware: `puck-v0.1.0`

## Hardware

| Part | Detail |
| --- | --- |
| Board | Waveshare ESP32-S3-Touch-LCD-1.85C V2 (Rev 2.0) |
| Display | ST77916 360x360 round, QSPI, Waveshare official init sequence |
| Audio | ES8311 DAC (0x18), ES7210 mic ADC (0x40), NS4150B amp enabled on GPIO15 |
| I2S (shared) | MCLK GPIO2, BCLK GPIO48, LRCK GPIO38, DOUT GPIO47, DIN GPIO39 |
| I2C | SDA GPIO11, SCL GPIO10; PCA9554 IO expander at 0x20 |

## Layout

```
compose.yaml              Home Assistant, ESPHome, whisper, piper (all on prometheus)
open-firewall.sh          ufw rules the stack needs (run with sudo)
esphome/smart-puck.yaml   Puck firmware config (V2 adaptation of Lee's smart-puck.yaml)
esphome/backgrounds/      Images compiled into the firmware
homeassistant/            configuration.yaml + packages/smart_puck.yaml (forecast ring, music, grouping)
scripts/                  test.sh and git hooks
```

Secrets are **not** in the repo. Copy `esphome/secrets.example.yaml` to `esphome/secrets.yaml` and fill in Wi-Fi, `api_key` and `ota_password`. `esphome.env` holds the ESPHome dashboard login.

## Credits and license

Built on Lee Milstein's [esphome-smart-puck](https://github.com/LCMilstein/esphome-smart-puck) (MIT, commit `6d1fc51`). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The V2 audio and display settings were cross-checked against Waveshare's V2 documentation and community V2 configs (kept locally in `ref/`, not published). This repo is MIT licensed. See [LICENSE](LICENSE).

## Running the stack

```bash
cd ~/smartpuck
docker compose up -d
sudo ./open-firewall.sh        # once: opens 8123, 6052, 5353/udp, 1400 (Sonos push) to the LAN
```

| Service | Address |
| --- | --- |
| Home Assistant | http://192.168.1.21:8123 |
| ESPHome dashboard | http://192.168.1.21:6052 |
| Whisper / Piper | 127.0.0.1:10300 / 127.0.0.1:10200 (Wyoming) |
| Puck | 192.168.1.221 (reserved on the Fios router) |

## Flashing the puck

Over the air (normal):

```bash
docker exec esphome esphome run /config/smart-puck.yaml --device 192.168.1.221 --no-logs
```

USB (first flash or recovery), from the Mac:

```bash
source ~/esptool-venv/bin/activate
esptool --chip esp32s3 --port /dev/cu.usbmodem1101 write-flash 0x0 smart-puck.factory.bin
```

## Making changes

Every change goes on a branch, passes the tests, and merges through a pull request. The full process is in the [version control plan](https://claude.ai/artifact/GPqonfNn1vs8G6F9TtKxRg).

```bash
git switch -c feat/<short-name>
# edit, then:
git diff
scripts/test.sh
git commit -m "puck: <what changed>"
scripts/pr.py open --gates 1,2,3,4,5,6,7   # pushes (hooks run the tests) and opens the PR
scripts/pr.py status <number>              # files changed, mergeable, any unticked gates
scripts/pr.py merge <number>               # squash-merge, delete branch, sync main
```

`pr.py` needs a fine-grained GitHub token for this repo only (Contents and Pull requests: read/write) at `~/.config/smartpuck/github-token`, mode 600. `--gates` ticks those checkboxes; the rest are marked n/a. `merge` refuses while any gate is unticked. Merging in the GitHub web UI still works too.

**Each merge must update these docs:**

- `CHANGELOG.md`: one plain-English line under "Unreleased"
- `README.md`: whatever a person would now see or do differently (features, addresses, commands, hardware)
- `CLAUDE.md`: whatever Claude would now need to know (new files, entities, gotchas, commands)

The pre-push hook refuses a push that changes config files without touching these docs. If a change truly needs no doc update, put `docs: none` in the commit message.

## Backups

Everything not in git (Home Assistant's `.storage` and all secrets files) is backed up nightly at 3:15 AM by `scripts/backup.sh` (cron) to `~/smartpuck-backups/nightly/`, keeping 14 days. Each backup is verified after writing. The log is `~/smartpuck-backups/backup.log`. History (`home-assistant_v2.db`) is not included.

These backups live on the same disk as the stack. Copying them off-box is a later improvement.

Restore (restore tested 2026-11-14 into an isolated container):

```bash
scripts/backup.sh --verify ~/smartpuck-backups/nightly/<file>.tar   # check it first
docker compose stop homeassistant esphome
mkdir /tmp/r && tar xf <file>.tar -C /tmp/r
sudo tar xzf /tmp/r/homeassistant.tgz -C homeassistant/
sudo tar xzf /tmp/r/esphome.tgz -C esphome/
cp /tmp/r/esphome.env . && chmod 600 esphome.env
docker compose start homeassistant esphome
```

## Testing

`scripts/test.sh` runs the automatic gates: stack file, puck config, firmware compile and HA config check. After flashing, work through the on-device checklist: clock, weather ring, tap cycle, music, voice, and no error loops in the logs. Both are described in the plan.
