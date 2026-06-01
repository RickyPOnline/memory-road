#!/usr/bin/env bash
# boot_brief.sh · SessionStart hook · auto "where are we?" answer
# Fires once at session boot · injects live Memory Road status + top unfinished
# items BEFORE the agent sees a user prompt · agent lands knowing exactly
# what to continue without operator having to type "where are we?"
#
# Per the operator 2026-05-30 · "I don't want to have to type 'where are we' · this
# should be done automatically · in a way that if you know nothing you do it
# automatically."
set -u

DB=${MEMORY_ROAD_DB:-$HOME/.memory_road/continuity_kernel.db}
CONTROL=$HOME/.memory_road/runtime/memory_road_control.sh

echo ""
echo "━━━ MEMORY ROAD · BOOT BRIEF · AUTO-INJECTED ━━━"
echo ""
echo "📊 LIVE STATE ·"

if [ -f "$DB" ]; then
  sqlite3 "$DB" "
    SELECT '  L3 summaries:     ' || COUNT(*) FROM episode_summaries;
    SELECT '  L3 missing:       ' || (SELECT COUNT(*) FROM episodes_v2 WHERE id NOT IN (SELECT episode_v2_id FROM episode_summaries));
    SELECT '  Batch writes:     ' || COUNT(*) FROM episode_summaries WHERE writer_model LIKE '%BATCH%';
  "
  HUNTS=$(sqlite3 "$DB" "SELECT COUNT(*) FROM huntsman_flags WHERE status='open';" 2>/dev/null || echo "0")
  echo "  HUNTSMAN open:    $HUNTS"
  CLUST=$(sqlite3 "$DB" "SELECT COUNT(DISTINCT cluster_id) FROM episode_clusters;" 2>/dev/null || echo "0")
  echo "  CARTO clusters:   $CLUST"
fi

# Worker liveness
ROTATOR=$(pgrep -f "chronicler_rotator_manager" 2>/dev/null | wc -l)
SWEEPER=$(pgrep -f "chronicler_forward_sweeper" 2>/dev/null | wc -l)
WORKERS=$(ps -ef | grep "python3 -u" | grep -v grep | wc -l)
echo "  Rotator:          $([ $ROTATOR -gt 0 ] && echo "🟢 alive" || echo "⚪ stopped (window cap likely)")"
echo "  Forward sweeper:  $([ $SWEEPER -gt 0 ] && echo "🟢 alive" || echo "⚪ stopped")"
echo "  Active workers:   $WORKERS"

# Cortex packet age
PACKET=$HOME/.claude/projects/<project-id>/memory/project_continuity_state.md
if [ -f "$PACKET" ]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$PACKET") ))
  echo "  Cortex packet:    ${AGE}s old · $([ $AGE -lt 300 ] && echo "🟢 fresh" || echo "🟡 stale")"
fi

echo ""
echo "🐕 TOP 5 UNFINISHED (HUNTSMAN) ·"
if [ -f "$DB" ]; then
  sqlite3 -separator '|' "$DB" "
    SELECT '  · ' || substr(description, 1, 100) FROM huntsman_flags
    WHERE status='open'
    ORDER BY last_seen DESC LIMIT 5;
  " 2>/dev/null | sed 's/|/ /g'
fi

echo ""
echo "🔔 CRITICAL BOOT ACTIONS ·"
echo "  1. ARM TELEGRAM MONITOR · run this tool call as your FIRST action ·"
echo "     Monitor(command=\"tail -n 0 -f $HOME/.memory_road/runtime/ccode_inbox.txt 2>/dev/null | grep --line-buffered '.'\", persistent=true, timeout_ms=3600000)"
echo "  2. After Monitor armed · read the cortex packet above for current state"
echo "  3. Continue work · do NOT ask 'where are we' · the brief above IS the answer"
echo ""
echo "━━━ END BOOT BRIEF ━━━"
echo ""
