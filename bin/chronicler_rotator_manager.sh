#!/usr/bin/env bash
# Chronicler Rotator Manager · per the operator's 4-staggered-rotate strategy.
#
# - 4 slots (A B C D)
# - Each slot runs ONE worker at a time
# - Workers exit after MAX_SUMMARIES_PER_ROTATION → FRESH context dir → relaunch
# - 5-consec-fail (cap hit) → slot cooldown COOLDOWN_SEC then probe + resume
# - Slabs episode-id range into chunks · slots claim next free chunk
# - Telegram beacon every BEACON_EVERY total summaries
# - Manager exits when 0 episodes remain missing
#
# Per `feedback_never_kill_progress_adapt_at_transitions_LOCKED.md` ·
# this is the v2 strategy that takes over after Wave 2 dies naturally.
set -u

# === CONFIG ===
SLOTS=(A B C D)
SLAB_SIZE=150               # episodes per slab (some will already be done)
MAX_SUMMARIES_PER_ROTATION=50  # fresh context every 50 summaries
STAGGER_SEC=300             # 5 min between slot starts on initial fan-out
COOLDOWN_SEC=900            # 15 min cooldown when slot hits cap
PACE_SEC=3                  # pace between calls within worker
PROBE_TIMEOUT=25            # max sec for window-probe call
BEACON_EVERY=500            # Telegram beacon every N summaries
STATE_DIR=/tmp/chronicler_rotator_state
LOG=/tmp/chronicler_rotator_manager.log
DB=${MEMORY_ROAD_DB:-$HOME/.memory_road/continuity_kernel.db}
SLOT_WORKER=$HOME/.memory_road/runtime/fire_chronicler_slot_worker.sh

mkdir -p "$STATE_DIR"
echo "$(date -Iseconds) · ROTATOR MANAGER START" >> "$LOG"

tg() {
  echo "[WAVE ROTATOR] $1" >> $HOME/.memory_road/runtime/ccode_telegram_outbox.txt 2>/dev/null
}

# === SLAB ALLOCATOR ===
# Build the slab queue · find all missing-summary IDs · group into slabs
build_slabs() {
  sqlite3 "$DB" "SELECT id FROM episodes_v2 WHERE id NOT IN (SELECT episode_v2_id FROM episode_summaries) ORDER BY id ASC" > "$STATE_DIR/missing_ids.txt"
  TOTAL=$(wc -l < "$STATE_DIR/missing_ids.txt")
  echo "$(date -Iseconds) · slabs · total_missing=$TOTAL slab_size=$SLAB_SIZE" >> "$LOG"

  > "$STATE_DIR/slabs.txt"
  awk -v size=$SLAB_SIZE '
    NR==1 { start=$1; cnt=1; next }
    { cnt++; if (cnt > size) { print start"-"prev; start=$1; cnt=1 } prev=$1 }
    END { if (NR>0) print start"-"prev }
  ' "$STATE_DIR/missing_ids.txt" > "$STATE_DIR/slabs.txt"

  NSLABS=$(wc -l < "$STATE_DIR/slabs.txt")
  echo "$(date -Iseconds) · slabs · count=$NSLABS" >> "$LOG"
  > "$STATE_DIR/slabs_done.txt"
  > "$STATE_DIR/slabs_claimed.txt"
}

# Get next free slab · atomic-ish via flock
next_slab() {
  local SLAB
  (
    flock 200
    while read -r CAND; do
      if ! grep -qxF "$CAND" "$STATE_DIR/slabs_claimed.txt" 2>/dev/null; then
        echo "$CAND" >> "$STATE_DIR/slabs_claimed.txt"
        echo "$CAND"
        break
      fi
    done < "$STATE_DIR/slabs.txt"
  ) 200>"$STATE_DIR/slabs.lock"
}

# Probe window state · returns 0 if open, 1 if capped
probe_window() {
  cd /root/.probe_window 2>/dev/null || mkdir -p /root/.probe_window && cd /root/.probe_window
  local REPLY
  REPLY=$(timeout $PROBE_TIMEOUT claude -p --output-format text "Reply with only the word ALIVE" 2>/dev/null)
  if echo "$REPLY" | grep -qi ALIVE; then
    return 0
  fi
  return 1
}

# Count total summaries written
count_summaries() {
  sqlite3 "$DB" "SELECT COUNT(*) FROM episode_summaries;"
}

# Build initial slabs
build_slabs
INITIAL_MISSING=$(wc -l < "$STATE_DIR/missing_ids.txt")
INITIAL_SUMMARIES=$(count_summaries)
echo "$(date -Iseconds) · INITIAL · missing=$INITIAL_MISSING summaries=$INITIAL_SUMMARIES" >> "$LOG"
tg "Rotator MANAGER online · 4 slots · missing=$INITIAL_MISSING · target ETA 3-5 days · ride the cycles"

# === ROTATION COUNTERS PER SLOT ===
declare -A ROTATION
declare -A SLOT_PID
declare -A SLOT_SLAB
declare -A SLOT_COOLDOWN_UNTIL
for S in "${SLOTS[@]}"; do
  ROTATION[$S]=0
  SLOT_PID[$S]=0
  SLOT_SLAB[$S]=""
  SLOT_COOLDOWN_UNTIL[$S]=0
done

LAST_BEACON=$INITIAL_SUMMARIES
LAST_PROGRESS_LOG=$(date +%s)

# === STAGGERED INITIAL LAUNCH ===
echo "$(date -Iseconds) · STAGGERED LAUNCH" >> "$LOG"
SLOT_IDX=0
for S in "${SLOTS[@]}"; do
  if [ $SLOT_IDX -gt 0 ]; then
    echo "$(date -Iseconds) · staggering ${STAGGER_SEC}s before slot $S" >> "$LOG"
    sleep $STAGGER_SEC
  fi
  SLAB=$(next_slab)
  if [ -z "$SLAB" ]; then
    echo "$(date -Iseconds) · no slabs left at initial launch · slot $S idle" >> "$LOG"
    break
  fi
  ROTATION[$S]=$((ROTATION[$S] + 1))
  START=$(echo $SLAB | cut -d- -f1)
  END=$(echo $SLAB | cut -d- -f2)
  SLOT_SLAB[$S]=$SLAB
  setsid nohup bash "$SLOT_WORKER" "$S" "${ROTATION[$S]}" "$START" "$END" "$MAX_SUMMARIES_PER_ROTATION" "$PACE_SEC" </dev/null >>"$LOG" 2>&1 &
  SLOT_PID[$S]=$!
  echo "$(date -Iseconds) · LAUNCHED slot=$S R=${ROTATION[$S]} slab=$SLAB pid=${SLOT_PID[$S]}" >> "$LOG"
  tg "Slot $S R${ROTATION[$S]} fired · slab=$SLAB"
  SLOT_IDX=$((SLOT_IDX + 1))
done

# === MAIN LOOP ===
while true; do
  NOW=$(date +%s)
  MISSING=$(sqlite3 "$DB" "SELECT COUNT(*) FROM episodes_v2 WHERE id NOT IN (SELECT episode_v2_id FROM episode_summaries);")

  if [ "$MISSING" -eq 0 ]; then
    echo "$(date -Iseconds) · ZERO MISSING · all done" >> "$LOG"
    tg "🎯 CHRONICLER L3 = ZERO MISSING · job done · rotator exiting"
    exit 0
  fi

  # Periodic progress log (every 5 min)
  if [ $((NOW - LAST_PROGRESS_LOG)) -ge 300 ]; then
    SUMS=$(count_summaries)
    echo "$(date -Iseconds) · PROGRESS · missing=$MISSING summaries=$SUMS" >> "$LOG"
    LAST_PROGRESS_LOG=$NOW
  fi

  # Telegram beacon
  SUMS=$(count_summaries)
  if [ $((SUMS - LAST_BEACON)) -ge $BEACON_EVERY ]; then
    DELTA=$((SUMS - LAST_BEACON))
    tg "Beacon · summaries=$SUMS (+$DELTA) · missing=$MISSING"
    LAST_BEACON=$SUMS
  fi

  # Check each slot
  for S in "${SLOTS[@]}"; do
    PID=${SLOT_PID[$S]}
    # Skip slot if cooldown active
    if [ $NOW -lt ${SLOT_COOLDOWN_UNTIL[$S]} ]; then
      continue
    fi
    # Check if worker is alive
    if [ "$PID" -ne 0 ] && kill -0 $PID 2>/dev/null; then
      continue  # still running
    fi
    # Worker has exited · read exit marker if present
    LOWER=$(echo "$S" | tr '[:upper:]' '[:lower:]')
    MARKER="/tmp/chronicler_slot_${LOWER}_r${ROTATION[$S]}.exit"
    EXIT_REASON="unknown"
    if [ -f "$MARKER" ]; then
      EXIT_REASON=$(python3 -c "import json; d=json.load(open('$MARKER')); print(d['exit_reason'])" 2>/dev/null || echo "unknown")
    fi
    echo "$(date -Iseconds) · slot=$S R=${ROTATION[$S]} exit=$EXIT_REASON" >> "$LOG"

    # Decide next action
    if [ "$EXIT_REASON" = "cap_hit" ]; then
      SLOT_COOLDOWN_UNTIL[$S]=$((NOW + COOLDOWN_SEC))
      echo "$(date -Iseconds) · slot=$S cooldown until $(date -d @${SLOT_COOLDOWN_UNTIL[$S]} -u +%H:%M:%S) UTC" >> "$LOG"
      SLOT_PID[$S]=0
      continue
    fi

    # rotation_complete or range_exhausted · claim next slab
    SLAB=$(next_slab)
    if [ -z "$SLAB" ]; then
      echo "$(date -Iseconds) · slot=$S no slabs left · idle" >> "$LOG"
      SLOT_PID[$S]=0
      continue
    fi
    ROTATION[$S]=$((ROTATION[$S] + 1))
    START=$(echo $SLAB | cut -d- -f1)
    END=$(echo $SLAB | cut -d- -f2)
    SLOT_SLAB[$S]=$SLAB
    setsid nohup bash "$SLOT_WORKER" "$S" "${ROTATION[$S]}" "$START" "$END" "$MAX_SUMMARIES_PER_ROTATION" "$PACE_SEC" </dev/null >>"$LOG" 2>&1 &
    SLOT_PID[$S]=$!
    echo "$(date -Iseconds) · ROTATE slot=$S R=${ROTATION[$S]} slab=$SLAB pid=${SLOT_PID[$S]}" >> "$LOG"
  done

  sleep 30
done
