#!/usr/bin/env bash
# Chronicler Forward Sweeper · keeps Memory Road's now-forward edge clean.
#
# Per Ricky 2026-05-29 23:40 UTC · "what implementations have you made to
# keep memory from now forward up to date?"
#
# Polls every 5 min for episodes_v2 with id > watermark AND no summary ·
# batch-summarizes them via chronicler_batch (BATCH=5 · blank slate worker
# dir · empty CLAUDE.md stub). Independent of the backlog rotator · runs
# FOREVER · stays small · doesn't compete for the bucket because there are
# only a few new episodes per cycle.
#
# Per `feedback_blank_slate_per_agent_LOCKED.md` and
#     `feedback_snow_plow_pattern_right_now_backward_LOCKED.md`.
set -u

DIR=/root/.forward_sweeper
mkdir -p "$DIR"
touch "$DIR/CLAUDE.md"  # blank slate · block walk-up
LOG=/tmp/chronicler_forward_sweeper.log
WATERMARK=/tmp/chronicler_forward_sweeper.watermark
DB=${MEMORY_ROAD_DB:-$HOME/.memory_road/continuity_kernel.db}
POLL_SEC=300  # 5 min

echo "$(date -Iseconds) · FORWARD SWEEPER START" >> "$LOG"

tg() {
  echo "[WAVE FORWARD-SWEEPER] $1" >> $HOME/.memory_road/runtime/ccode_telegram_outbox.txt 2>/dev/null
}

# Initialize watermark to current newest episode if not set
if [ ! -f "$WATERMARK" ]; then
  NEWEST=$(sqlite3 $DB "SELECT MAX(id) FROM episodes_v2;")
  echo "$NEWEST" > "$WATERMARK"
  echo "$(date -Iseconds) · INIT watermark=$NEWEST" >> "$LOG"
fi

cd "$DIR"
export PYTHONPATH="/root/wc/workspace/skills:${PYTHONPATH:-}"

while true; do
  WM=$(cat "$WATERMARK" 2>/dev/null || echo 0)

  # Find new episodes since watermark that have no summary
  NEW_IDS=$(sqlite3 $DB "SELECT id FROM episodes_v2 WHERE id > $WM AND id NOT IN (SELECT episode_v2_id FROM episode_summaries) ORDER BY id ASC LIMIT 20;")

  if [ -z "$NEW_IDS" ]; then
    echo "$(date -Iseconds) · no new episodes · watermark=$WM" >> "$LOG"
  else
    COUNT=$(echo "$NEW_IDS" | wc -l)
    NEW_MAX=$(echo "$NEW_IDS" | tail -1)
    echo "$(date -Iseconds) · processing $COUNT new episodes · ids=$(echo $NEW_IDS | tr '\n' ',')" >> "$LOG"

    # Build python list literal · batch through chronicler_batch
    IDS_PY=$(echo "$NEW_IDS" | tr '\n' ',' | sed 's/,$//')
    python3 -u -c "
import sys
sys.path.insert(0, '/root/wc/workspace/skills')
from chronicler_batch import summarize_batch

ids = [$IDS_PY]
# Process in batches of 5
ok_total = 0
fail_total = 0
for i in range(0, len(ids), 5):
    batch = ids[i:i+5]
    result = summarize_batch(batch)
    ok_total += len(result.get('ok', []))
    fail_total += len(result.get('fail', []))
    print(f'  forward batch={batch} · OK={len(result.get(\"ok\", []))} FAIL={len(result.get(\"fail\", []))}', flush=True)
print(f'FINAL · forward sweep · OK={ok_total} FAIL={fail_total}', flush=True)
" >> "$LOG" 2>&1

    # Advance watermark only to LAST processed (failed ones stay before watermark for retry)
    echo "$NEW_MAX" > "$WATERMARK"
    if [ "$COUNT" -gt 0 ]; then
      tg "Forward sweep · $COUNT new episodes summarized · watermark=$NEW_MAX"
    fi
  fi

  sleep $POLL_SEC
done
