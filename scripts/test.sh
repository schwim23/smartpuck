#!/usr/bin/env bash
# Automatic gates 2-5 from the version control plan. Stops at the first failure.
#   scripts/test.sh          all gates (includes firmware compile, 2-10 min)
#   scripts/test.sh --quick  skip the compile
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
QUICK=0; [[ "${1:-}" == "--quick" ]] && QUICK=1
pass() { printf '\033[32mPASS\033[0m %s\n' "$1"; }
fail() { printf '\033[31mFAIL\033[0m %s\n' "$1"; exit 1; }

docker compose config -q && pass "Gate 2: compose.yaml valid" || fail "Gate 2: compose.yaml invalid"

out=$(docker exec esphome esphome config /config/smart-puck.yaml 2>&1) \
  && pass "Gate 3: ESPHome config valid" \
  || { echo "$out" | tail -30; fail "Gate 3: ESPHome config invalid"; }

if [[ $QUICK -eq 0 ]]; then
  echo "     Gate 4: compiling firmware (2-10 min)..."
  out=$(docker exec esphome esphome compile /config/smart-puck.yaml 2>&1) \
    || { echo "$out" | tail -40; fail "Gate 4: firmware compile failed"; }
  ram=$(echo "$out"   | grep -oP 'RAM:.*?\K[0-9.]+(?=%)'   | tail -1)
  flash=$(echo "$out" | grep -oP 'Flash:.*?\K[0-9.]+(?=%)' | tail -1)
  awk -v r="$ram" -v f="$flash" 'BEGIN{exit !(r<80 && f<90)}' \
    && pass "Gate 4: firmware compiles (RAM ${ram}%, flash ${flash}%)" \
    || fail "Gate 4: over budget (RAM ${ram}% must be <80, flash ${flash}% must be <90)"
else
  echo "SKIP Gate 4: compile (--quick)"
fi

out=$(docker exec homeassistant python -m homeassistant --script check_config --config /config 2>&1) \
  && ! echo "$out" | grep -qiE 'invalid config|error' \
  && pass "Gate 5: Home Assistant config valid" \
  || { echo "$out" | tail -30; fail "Gate 5: Home Assistant config has errors"; }

echo "Automatic gates passed. Gate 6 (on-device smoke test) and Gate 7 (docs) are still on you."
