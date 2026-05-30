#!/usr/bin/env bash
# memory_road_control.sh · pause/resume/status for the Memory Road worker fleet.
#
# Per `feedback_never_kill_progress_adapt_at_transitions_LOCKED.md` ·
# PAUSE = signal manager to STOP after current rotations finish naturally.
# RESUME = re-fire manager · picks up next slab cleanly.
# STATUS = what's alive · what's not · how much progress today.
#
# Pre-window-reset routine ·
#   bash memory_road_control.sh pause      # before Anthropic Max reset
#   ... do priority work in main agent ...
#   bash memory_road_control.sh resume     # after reset · plows resume
set -u

ACTION="${1:-status}"
ROTATOR_SCRIPT=$HOME/.memory_road/runtime/chronicler_rotator_manager.sh
SWEEPER_SCRIPT=$HOME/.memory_road/runtime/chronicler_forward_sweeper.sh
WATCHDOG_SCRIPT=$HOME/.memory_road/runtime/chronicler_window_watchdog.sh
PAUSE_FLAG=/tmp/memory_road_pause.flag
LOG=/tmp/memory_road_control.log
DB=${MEMORY_ROAD_DB:-$HOME/.memory_road/continuity_kernel.db}

log() {
  echo "[$(date -Iseconds)] $1" | tee -a $LOG
}

tg() {
  echo "[MEMORY ROAD] $1" >> $HOME/.memory_road/runtime/ccode_telegram_outbox.txt 2>/dev/null
}

count_workers() {
  ps -ef | grep -E "fire_chronicler_slot|chronicler_rotator|chronicler_forward|huntsman|cartographer|miner_smith" | grep -v grep | wc -l
}

case "$ACTION" in
  pause)
    log "PAUSE requested"
    touch $PAUSE_FLAG

    # Kill the manager (it's just a coordinator · in-flight workers continue)
    log "  killing rotator manager · in-flight workers will finish their rotations naturally"
    pkill -f "$ROTATOR_SCRIPT" 2>/dev/null

    # Optionally kill forward sweeper (if you want zero token consumption)
    if [ "${2:-}" = "all" ]; then
      log "  killing forward sweeper too (--all mode)"
      pkill -f "$SWEEPER_SCRIPT" 2>/dev/null
      pkill -f "$WATCHDOG_SCRIPT" 2>/dev/null
    fi

    sleep 3
    ALIVE=$(count_workers)
    log "  workers still running (finishing rotation): $ALIVE"
    log "  PAUSE complete · run 'resume' to relaunch"
    tg "Memory Road PAUSED · $ALIVE workers finishing current rotations"
    ;;

  resume)
    log "RESUME requested"
    rm -f $PAUSE_FLAG

    # Check what's already running so we don't double-fire
    ROTATOR_ALIVE=$(pgrep -f "$ROTATOR_SCRIPT" | wc -l)
    SWEEPER_ALIVE=$(pgrep -f "$SWEEPER_SCRIPT" | wc -l)

    if [ "$ROTATOR_ALIVE" -eq 0 ]; then
      log "  firing rotator manager"
      setsid nohup bash $ROTATOR_SCRIPT </dev/null >/tmp/chronicler_rotator_outer.log 2>&1 &
      disown
    else
      log "  rotator already alive · skipping"
    fi

    if [ "$SWEEPER_ALIVE" -eq 0 ]; then
      log "  firing forward sweeper"
      setsid nohup bash $SWEEPER_SCRIPT </dev/null >/tmp/chronicler_forward_sweeper_outer.log 2>&1 &
      disown
    else
      log "  forward sweeper already alive · skipping"
    fi

    sleep 3
    ALIVE=$(count_workers)
    log "  RESUME complete · workers alive: $ALIVE"
    tg "Memory Road RESUMED · $ALIVE workers fired"
    ;;

  status)
    echo "=== MEMORY ROAD STATUS ==="
    echo ""

    # Pause flag
    if [ -f $PAUSE_FLAG ]; then
      echo "  STATE: 🟡 PAUSED (run 'resume' to relaunch)"
    else
      echo "  STATE: 🟢 ACTIVE"
    fi
    echo ""

    # Substrate
    echo "  L0 substrate · continuity-kernel.service · $(systemctl is-active continuity-kernel 2>/dev/null || echo 'unknown')"

    # Workers
    ROTATOR=$(pgrep -f "$ROTATOR_SCRIPT" | wc -l)
    SWEEPER=$(pgrep -f "$SWEEPER_SCRIPT" | wc -l)
    WORKERS=$(ps -ef | grep "python3 -u" | grep -v grep | wc -l)

    echo "  Rotator manager       · $([ $ROTATOR -gt 0 ] && echo "🟢 alive (PID $(pgrep -f $ROTATOR_SCRIPT | head -1))" || echo "⚪ stopped")"
    echo "  Forward sweeper       · $([ $SWEEPER -gt 0 ] && echo "🟢 alive (PID $(pgrep -f $SWEEPER_SCRIPT | head -1))" || echo "⚪ stopped")"
    echo "  Worker subprocesses   · $WORKERS"

    echo ""
    echo "=== L3 PROGRESS ==="
    sqlite3 $DB "
      SELECT '  Episodes total       · ' || COUNT(*) FROM episodes_v2;
      SELECT '  Summaries written    · ' || COUNT(*) FROM episode_summaries;
      SELECT '  Missing summaries    · ' || (SELECT COUNT(*) FROM episodes_v2 WHERE id NOT IN (SELECT episode_v2_id FROM episode_summaries));
      SELECT '  Batch-mode writes    · ' || COUNT(*) FROM episode_summaries WHERE writer_model LIKE '%BATCH%';
      SELECT '  Summaries last hour  · ' || COUNT(*) FROM episode_summaries WHERE written_at > strftime('%s','now') - 3600;
    "

    echo ""
    echo "=== HIGHER LAYERS ==="
    sqlite3 $DB "
      SELECT '  HUNTSMAN open flags  · ' || COUNT(*) FROM huntsman_flags WHERE status='open';
    " 2>/dev/null
    sqlite3 $DB "
      SELECT '  CARTOGRAPHER assigned· ' || COUNT(*) FROM episode_clusters;
    " 2>/dev/null
    sqlite3 $DB "
      SELECT '  MINER+SMITH candidates· ' || COUNT(*) FROM candidate_doctrines;
    " 2>/dev/null

    echo ""
    echo "=== CORTEX PACKET ==="
    PACKET=$HOME/.claude/projects/<project-id>/memory/project_continuity_state.md
    if [ -f $PACKET ]; then
      AGE=$(( $(date +%s) - $(stat -c %Y $PACKET) ))
      echo "  Last update          · ${AGE}s ago · $([ $AGE -lt 600 ] && echo "🟢 fresh" || echo "🟡 stale")"
    else
      echo "  Packet               · ⚪ missing (L5 WATCHER not running?)"
    fi
    ;;

  burn-test)
    # Burn an entire window cycle deliberately · for stress testing
    echo "BURN-TEST · fires extra workers · use only when you want to drain the bucket fast"
    echo "  (e.g., before a planned window reset to force the bucket to refill cleanly)"
    bash $ROTATOR_SCRIPT &
    bash $ROTATOR_SCRIPT &
    bash $ROTATOR_SCRIPT &
    bash $ROTATOR_SCRIPT &
    echo "  4 extra rotator instances fired · let them burn"
    ;;

  *)
    echo "Usage · memory_road_control.sh <action>"
    echo ""
    echo "Actions ·"
    echo "  pause           Stop rotator · in-flight workers finish naturally"
    echo "  pause all       Stop rotator + forward sweeper + watchdog (zero token use)"
    echo "  resume          Re-fire rotator + sweeper · pick up where left off"
    echo "  status          Show what's alive · progress · cortex packet age"
    echo "  burn-test       Fire extra workers to drain bucket (testing)"
    ;;
esac
