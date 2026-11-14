#!/usr/bin/env bash
# Nightly backup of everything that is NOT in git: Home Assistant state (.storage: integrations,
# devices, users, Assist pipelines, dashboards) and every secrets file. Keeps 14 days.
#   scripts/backup.sh                 make a backup, verify it, prune old ones
#   scripts/backup.sh --verify FILE   check an existing backup restores cleanly (to a temp dir)
# Output: ~/smartpuck-backups/nightly/smartpuck-YYYY-MM-DD_HHMM.tar (mode 600, contains secrets)
# Not included: home-assistant_v2.db (history only; copying it live risks a torn SQLite file).
set -euo pipefail
DEST="$HOME/smartpuck-backups/nightly"; KEEP_DAYS=14
umask 077

verify() {
  local f="$1" t; t=$(mktemp -d); trap 'rm -rf "$t"' RETURN
  tar xf "$f" -C "$t"
  mkdir "$t/ha" "$t/esp"
  tar xzf "$t/homeassistant.tgz" -C "$t/ha"
  tar xzf "$t/esphome.tgz" -C "$t/esp"
  python3 - "$t" <<'PY'
import json, sys, os
t = sys.argv[1]
entries = json.load(open(f"{t}/ha/.storage/core.config_entries"))["data"]["entries"]
domains = sorted({e["domain"] for e in entries})
for need in ("esphome", "wyoming", "sonos"):
    assert need in domains, f"missing {need} integration in backup"
for f in ("ha/secrets.yaml", "esp/secrets.yaml", "esphome.env"):
    assert os.path.getsize(f"{t}/{f}") > 0, f"{f} empty"
n = len(os.listdir(f"{t}/ha/.storage"))
print(f"verify OK: {n} .storage files, {len(entries)} integrations ({', '.join(domains[:8])}...), secrets present")
PY
}

if [[ "${1:-}" == "--verify" ]]; then verify "$2"; exit; fi

mkdir -p "$DEST"
out="$DEST/smartpuck-$(date +%F_%H%M).tar"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
docker exec homeassistant tar czf - -C /config .storage secrets.yaml > "$tmp/homeassistant.tgz"
docker exec esphome tar czf - -C /config secrets.yaml .device-builder-preferences.json > "$tmp/esphome.tgz"
cp "$HOME/smartpuck/esphome.env" "$tmp/"
tar cf "$out" -C "$tmp" homeassistant.tgz esphome.tgz esphome.env
chmod 600 "$out"
echo "$(date '+%F %T') wrote $out ($(du -h "$out" | cut -f1))"
verify "$out"
find "$DEST" -name 'smartpuck-*.tar' -mtime +"$KEEP_DAYS" -print -delete
