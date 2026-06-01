#!/usr/bin/env bash
# boot_arm_monitor_alert.sh · SessionStart hook · screams about Monitor.
# Fires once at session boot · injects an IMPOSSIBLE-TO-IGNORE alert that
# tells Claude to arm the Telegram Monitor as the very first action.
#
# Per the operator 2026-05-30 · "the MONITOR for telegram always needs to be on,
# its always reset and missing/off when you come back or clear or compact."
#
# Pairs with verify_monitor_armed.sh (UserPromptSubmit) · belt + suspenders.
set -u

# Always print the alert · Claude reads this BEFORE seeing the user
cat <<'ALERT'

🚨🚨🚨 SESSION BOOT · ARM TELEGRAM MONITOR BEFORE ANY OTHER ACTION 🚨🚨🚨

Per locked doctrine feedback_arm_monitor_on_session_boot_LOCKED.md ·
the operator's Telegram inbox MUST have a live tail pushing into your
context. If you skip this, operator messages queue silently and
operator goes deaf-silent.

EXECUTE THIS TOOL CALL FIRST · BEFORE ANYTHING ELSE ·

  Monitor(
    command="tail -n 0 -f $HOME/.memory_road/runtime/ccode_inbox.txt 2>/dev/null | grep --line-buffered '.'",
    persistent=True,
    timeout_ms=3600000,
    description="Telegram inbox real-time tail · slap Wave on every new line"
  )

Then proceed with the boot brief above and continue work.

🚨🚨🚨 ARM MONITOR · THEN PROCEED · DO NOT SKIP 🚨🚨🚨

ALERT
