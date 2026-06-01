#!/bin/bash
# boot_arm_monitor_daemon.sh · SessionStart hook · auto-arms a background
# tail watcher on the Telegram inbox so push works WITHOUT the model needing
# to invoke the Monitor tool. Belt+suspenders with inject_inbox.sh (UserPromptSubmit)
# and preinject_inbox.sh (PreToolUse). Locked 2026-05-31 per Ricky:
# "hard hook it when you start up, duh · I shouldn't have to tell you every time."
set -u
INBOX=/root/wc/runtime/ccode_inbox.txt
BUFFER=/tmp/wave_inbox_buffer.log
PIDFILE=/tmp/wave_inbox_daemon.pid
# Preserve healthy daemon · prior bug spawned a new tail every SessionStart
# without cleaning up · accumulated 463 leaked tails before catching it. Now:
# if the pid in PIDFILE is still alive AND its cmdline matches tail+inbox,
# REUSE IT instead of spawning a new one.
PRIOR_PID=$(cat "$PIDFILE" 2>/dev/null)
if [ -n "$PRIOR_PID" ] && kill -0 "$PRIOR_PID" 2>/dev/null; then
  CMDLINE=$(tr '\0' ' ' < /proc/$PRIOR_PID/cmdline 2>/dev/null)
  case "$CMDLINE" in
    tail*ccode_inbox*)
      echo "📨 INBOX DAEMON already alive · pid=$PRIOR_PID · reusing" >&2
      exit 0
      ;;
  esac
fi
# No healthy prior daemon · clear ANY stale tail watchers + start clean
# (correct pattern · ps cmd shows `tail -F /root/wc/runtime/ccode_inbox.txt`
# WITHOUT the redirect part · the old regex never matched anything)
pkill -TERM -f 'tail.*ccode_inbox.txt' 2>/dev/null || true
sleep 0.3
# Spawn fresh daemon · nohup survives session death · &disown detaches
nohup tail -F "$INBOX" >> "$BUFFER" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PIDFILE"
disown 2>/dev/null || true
# One-line ack to stderr so boot brief shows it
echo "📨 INBOX DAEMON ARMED · pid=$NEW_PID · tailing $INBOX → $BUFFER" >&2
exit 0
