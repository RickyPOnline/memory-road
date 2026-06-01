#!/usr/bin/env bash
# UserPromptSubmit hook · verify the Telegram inbox Monitor is armed AND fresh.
#
# Two failure modes this catches ·
#   1. MISSING · no tail process at all (fresh session · Wave forgot)
#   2. ORPHAN  · tail process exists but PPid=1 (reparented to init after
#                /compact killed its parent shell · OS process alive but
#                Monitor task-binding to Wave's context is severed)
#
# Per Ricky's directives ·
#   2026-05-26 23:38 UTC · "fix it so it never fucks up again"
#   2026-05-27 01:38 UTC · "as long as it doesn't make shit goofy"
#   2026-05-28 02:42 UTC · "fix it so it does not switch off every time you compact"
#
# The cortex/memory packet is delivered via inject_continuity_packet.sh hook on
# every UserPromptSubmit · NOT via a Monitor · because the kernel rewrites the
# packet every ~2 sec which floods Wave's context.

# Match EITHER pattern · Monitor tool's tail OR boot daemon's nohup tail
INBOX_PAT='tail .*ccode_inbox'
DAEMON_PIDFILE='/tmp/wave_inbox_daemon.pid'

DAEMON_PID=""
[ -f "$DAEMON_PIDFILE" ] && DAEMON_PID=$(cat "$DAEMON_PIDFILE" 2>/dev/null)

# Check: is daemon alive AND its cmdline still matches inbox tail?
DAEMON_OK="no"
if [ -n "$DAEMON_PID" ] && kill -0 "$DAEMON_PID" 2>/dev/null; then
  CMDLINE=$(tr '\0' ' ' < /proc/$DAEMON_PID/cmdline 2>/dev/null)
  case "$CMDLINE" in tail*ccode_inbox*) DAEMON_OK="yes" ;; esac
fi

STATUS="MISSING"
if [ "$DAEMON_OK" = "yes" ]; then
  STATUS="OK"  # Boot daemon is alive · push works regardless of Monitor tool state
else
  # No daemon · fall back to looking for ANY inbox-tail process (Monitor tool path)
  TAIL_PID=$(pgrep -f "$INBOX_PAT" 2>/dev/null | head -1)
  if [ -n "$TAIL_PID" ]; then
    PPID_VAL=$(awk '/^PPid:/ {print $2}' /proc/$TAIL_PID/status 2>/dev/null)
    if [ "$PPID_VAL" = "1" ]; then
      STATUS="ORPHAN"
    else
      STATUS="OK"
    fi
  fi
fi

if [ "$STATUS" = "OK" ]; then
  echo '{}'
  exit 0
fi

python3 - "$STATUS" <<'PY'
import json, sys
status = sys.argv[1]

if status == "ORPHAN":
    headline = "🚨🚨🚨 TELEGRAM MONITOR STALE POST-COMPACT · RE-ARM 🚨🚨🚨"
    sub = (
        "A tail process exists but was reparented to init (PPid=1).\n"
        "This happens after /compact · the OS process keeps running but\n"
        "Monitor's task-binding to Wave's notification stream was severed.\n"
        "Operator messages will queue silently until re-armed.\n"
    )
else:  # MISSING
    headline = "🚨🚨🚨 TELEGRAM INBOX MONITOR NOT ARMED · ARM BEFORE ANY OTHER WORK 🚨🚨🚨"
    sub = "No tail process found. Operator messages will queue silently.\n"

msg = (
    f"\n{headline}\n\n"
    f"{sub}\n"
    "EXECUTE ·\n"
    "  1. Bash · pkill -f '^tail -n 0 -f /root/wc/runtime/ccode_inbox'  (clear orphan)\n"
    "  2. Monitor(\n"
    "       command=\"tail -n 0 -f /root/wc/runtime/ccode_inbox.txt 2>/dev/null | grep --line-buffered '.'\",\n"
    "       persistent=True, timeout_ms=3600000,\n"
    "       description=\"Telegram inbox real-time tail · slap Wave on every new line\")\n"
    "\n"
    "Per locked doctrine feedback_arm_monitor_on_session_boot_LOCKED.md ·\n"
    "this is STEP 1 of every Wave session AND every post-compact resume.\n"
)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
PY
