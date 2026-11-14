# CLAUDE.md: Smart Puck

Instructions for Claude Code working in `~/smartpuck` on host `prometheus` (192.168.1.21). Read `README.md` for what the project is and how it's laid out.

## Keep the docs current (every merge and push)

Before any commit that will be pushed or merged, update:

1. `CHANGELOG.md`: one line under "Unreleased" saying what changed, in plain English.
2. `README.md`: features, addresses, commands, hardware or layout a person would notice changed.
3. `CLAUDE.md` (this file): new files, entity IDs, commands, gotchas or rules Claude needs next time.
4. The "Last updated" date and current firmware tag in `README.md` when firmware is tagged.

If nothing needs changing, say so in the commit message with `docs: none`. The pre-push hook enforces this. Never bypass it with `--no-verify` unless the user explicitly asks.

## Workflow rules

- Never commit directly to `main`. Use `feat/<name>`, `fix/<name>` or `docs/<name>` branches. Merge through a GitHub PR (squash).
- PRs from the CLI: `scripts/pr.py open --gates <gates that actually passed>`, then `status <n>` and `merge <n>`. Only tick gates that really ran. Gate 6 needs the user's confirmation. **Always ask the user before `merge`.** The token is at `~/.config/smartpuck/github-token`: never print, echo or commit it. If it expires (90 days), the user makes a new one.
- Before merging, run `scripts/test.sh` and get the user to confirm the on-device smoke checklist after an OTA flash.
- Commit prefixes: `puck:`, `ha:`, `stack:`, `docs:`.
- Ask before pushing, merging, tagging or flashing. Flashing changes a device in the user's kitchen.
- Switching branches changes the live config: the containers mount this folder. After abandoning a branch, switch back to `main` and reload HA.

## Secrets: never commit or print them

- `esphome/secrets.yaml` (Wi-Fi, `api_key`, `ota_password`), `homeassistant/secrets.yaml` and `esphome.env` (dashboard login) are gitignored.
- In configs, reference values with `!secret`. Update `secrets.example.yaml` with dummy values when adding a key.
- `homeassistant/.storage/` holds tokens. Never commit it.

## Commands and gotchas

- Validate: `docker exec esphome esphome config /config/smart-puck.yaml`
- Compile: `docker exec esphome esphome compile /config/smart-puck.yaml`
- OTA flash: `docker exec esphome esphome run /config/smart-puck.yaml --device 192.168.1.221 --no-logs`
- HA check: `docker exec homeassistant python -m homeassistant --script check_config --config /config`
- **Logs:** put the timeout *inside* the container, as in `docker exec esphome timeout 60 esphome logs /config/smart-puck.yaml --device 192.168.1.221`. An outer `timeout` orphans the process and fills the puck's API connection slots. The container has no `kill`. Use `python3 -c 'import os; os.kill(pid, 9)'`.
- Keep `logger` at INFO. DEBUG made the API connection drop.
- Files under `esphome/` and `homeassistant/` created by the containers are root-owned. Edit them via `docker exec` or ask the user to run `sudo`. `sudo` via `!` in-session doesn't work for this user, so give them commands to paste into a separate SSH tab.
- The ESPHome dashboard's "version history" setting is **off** (`version_history_enabled: false` in `esphome/.device-builder-preferences.json`). When on, it creates its own `esphome/.git`, which hides `esphome/` from this repo. Keep it off. If `esphome/.git` ever reappears, back it up with `git bundle` and remove it.
- Firewall changes go in `open-firewall.sh` (the user runs it with sudo). Sonos push needs TCP 1400 inbound.
- DHCP is the Verizon Fios router (192.168.1.1). UniFi is switches/APs only. Reservations ("Static lease type") exist for prometheus (.21) and the puck (.221).

## Device facts

- Board is **V2**. Lee's original config targets V1. Audio and display init were rewritten. Don't copy V1 pins or init back from `lee-src/`.
- Shared I2S bus, ES8311 DAC 0x18, ES7210 ADC 0x40 (mic channel left, 24dB), PA enable GPIO15 always on, 16 kHz.
- Display: ST77916 via `mipi_spi` at 40 MHz, Waveshare init sequence, reset on PCA9554 pin 2. The clock font needs every glyph it shows. "--:--" needed `-`.
- `thermostat_page` has `skip: true` (no climate entity yet). The occupancy sensor is missing, so the screen treats the room as occupied.
- Wake word: `hey_jarvis`. The user wants "Hey Bestie" later (needs microWakeWord training).

## Home Assistant

- Package: `homeassistant/packages/smart_puck.yaml` holds the forecast ring (from `weather.home` hourly; met.no has no `precipitation_probability`, so use `.get` with defaults), track progress, the `smart_puck_playpause` script, and the automation grouping `media_player.living_dining_living_dining` into `media_player.kitchen_kitchen`.
- Puck entities: `*.kitchen_smart_puck_*` (area Kitchen). The ESPHome entry must keep "Allow service calls" on.
- Assist pipeline "Puck": Wyoming whisper (127.0.0.1:10300) and piper (127.0.0.1:10200), HA conversation agent.

## Public repo

- `github.com/schwim23/smartpuck` is **public**. Never add secrets, tokens, Tailscale IPs, email addresses or other personal data.
- `ref/` (unlicensed community configs) stays local and gitignored. Third-party code goes in only with a compatible license, credited in `THIRD_PARTY_NOTICES.md`.
- Keep Lee's MIT notice in `THIRD_PARTY_NOTICES.md` while any of his code or images remain.
- `ALLOW_MAIN_PUSH=1` bypasses the pre-push main block. Use it only when the user explicitly asks.

## Plans

- Version control plan and feature backlog: https://claude.ai/artifact/GPqonfNn1vs8G6F9TtKxRg
- Build plan (phases 0–4): https://claude.ai/artifact/HeVjbMbtaJ7KJHU8Z4v5pX
