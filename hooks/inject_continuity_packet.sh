#!/usr/bin/env bash
# inject_continuity_packet.sh · UserPromptSubmit hook · injects L5 WATCHER cortex packet.
#
# Fires on every user prompt · reads project_continuity_state.md · injects it
# as additional_context. Agent sees the packet BEFORE the user message ·
# cannot skip memory.
#
# Per `feedback_memory_road_first_LOCKED.md` · this is STEP 1 of every prompt.
set -u

PACKET=${MEMORY_ROAD_PACKET:-$HOME/.claude/projects/<project-id>/memory/project_continuity_state.md}
LOG=/tmp/inject_continuity_packet.log
STALE_THRESHOLD_SEC=600  # 10 min · packet older than this triggers an alert

if [ ! -f "$PACKET" ]; then
  echo "⚠️ MEMORY ROAD packet missing · is continuity-kernel.service running?" 1>&2
  echo "$(date -Iseconds) · MISSING_PACKET" >> "$LOG"
  exit 0  # don't block the prompt
fi

NOW=$(date +%s)
MTIME=$(stat -c %Y "$PACKET")
AGE=$((NOW - MTIME))

# Inject the packet · wrapped in markers so it's unambiguous
echo "━━━ MEMORY ROAD · CONTINUITY PACKET (age=${AGE}s) ━━━"
cat "$PACKET"
echo "━━━ END PACKET ━━━"

# Stale-alert if packet is older than threshold
if [ "$AGE" -gt "$STALE_THRESHOLD_SEC" ]; then
  echo ""
  echo "🚨 PACKET STALE · age=${AGE}s > ${STALE_THRESHOLD_SEC}s · L5 WATCHER may be down"
  echo "   Run · systemctl status continuity-kernel"
fi

echo "$(date -Iseconds) · INJECT · packet_age=${AGE}s · packet_bytes=$(wc -c < $PACKET)" >> "$LOG"
