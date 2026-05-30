#!/usr/bin/env bash
# Window-watchdog · probes Anthropic subscription every 15 min
# When probe succeeds within 25s · auto-fires the 8 CHRONICLER workers
# and Telegram-alerts. Single-fire · exits after launch.
#
# Run detached: setsid nohup bash chronicler_window_watchdog.sh </dev/null > log 2>&1 &
set -u

LOG=/tmp/chronicler_window_watchdog.log
PROBE_DIR=/root/.probe_window
mkdir -p "$PROBE_DIR"

echo "$(date -Iseconds) · WATCHDOG START" >> "$LOG"

# Telegram helper
tg() {
  local MSG="$1"
  # write to outbox so listener forwards
  echo "[WAVE WATCHDOG] $MSG" >> $HOME/.memory_road/runtime/ccode_telegram_outbox.txt 2>/dev/null
}

PROBE_NUM=0
while true; do
  PROBE_NUM=$((PROBE_NUM + 1))
  cd "$PROBE_DIR"
  START=$(date +%s)
  REPLY=$(timeout 30 claude -p --output-format text "Reply with only the word ALIVE" 2>/dev/null)
  END=$(date +%s)
  ELAPSED=$((END - START))

  if echo "$REPLY" | grep -qi "ALIVE" && [ "$ELAPSED" -lt 25 ]; then
    echo "$(date -Iseconds) · WINDOW OPEN · probe#$PROBE_NUM · elapsed=${ELAPSED}s · firing workers" >> "$LOG"
    tg "Anthropic window OPEN at $(date -u +%H:%M:%S) · firing 8 CHRONICLERs · probe#$PROBE_NUM"

    # Fire the launcher fully detached
    setsid nohup bash /tmp/launch_chroniclers.sh </dev/null >/tmp/launch_chroniclers_relaunch.log 2>&1 &
    echo "$(date -Iseconds) · launcher fired pid=$!" >> "$LOG"

    sleep 20
    # Verify workers are up
    LIVE=$(ps -ef | grep "python3 -u -c" | grep -v grep | wc -l)
    echo "$(date -Iseconds) · LIVE workers after launch: $LIVE" >> "$LOG"
    tg "CHRONICLERs LIVE · $LIVE workers grinding"

    echo "$(date -Iseconds) · WATCHDOG EXIT" >> "$LOG"
    exit 0
  else
    echo "$(date -Iseconds) · probe#$PROBE_NUM · CAPPED · elapsed=${ELAPSED}s · reply_len=${#REPLY}" >> "$LOG"
  fi

  # Sleep 15 minutes between probes
  sleep 900
done
