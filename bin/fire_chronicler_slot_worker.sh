#!/usr/bin/env bash
# Slot worker · BATCH MODE · fires ONE rotation for ONE slot.
# Per `feedback_blank_slate_per_agent_LOCKED.md` and
#     `feedback_snow_plow_pattern_right_now_backward_LOCKED.md`.
#
# Each rotation processes batches of BATCH_SIZE episodes per Opus call ·
# strips CLAUDE.md walk-up via empty stub · counts each batched summary
# toward MAX_SUMMARIES target. ~5x fewer calls per summary stacked with
# ~3-4x CLAUDE.md savings = ~15-20x net throughput.
#
# Usage · fire_chronicler_slot_worker.sh <SLOT> <ROTATION> <START_ID> <END_ID> <MAX_SUMMARIES> <PACE_SEC>
set -u
SLOT="$1"
ROTATION="$2"
START="$3"
END="$4"
MAX="$5"
PACE="${6:-3}"
BATCH_SIZE="${BATCH_SIZE:-5}"

LOWER=$(echo "$SLOT" | tr '[:upper:]' '[:lower:]')
DIR="/root/.${LOWER}_r${ROTATION}"
mkdir -p "$DIR"
# Blank slate · empty CLAUDE.md blocks walk-up to $HOME/CLAUDE.md
touch "$DIR/CLAUDE.md"

export WAVE_WORKER_DIR="$DIR"
export WAVE_WORKER_NAME="${SLOT}_R${ROTATION}"
export PYTHONPATH="/root/wc/workspace/skills:${PYTHONPATH:-}"
export BATCH_SIZE

LOG="/tmp/chronicler_slot_${LOWER}_r${ROTATION}.log"
echo "$(date -Iseconds) · SLOT $SLOT R$ROTATION FIRE [BATCH=$BATCH_SIZE] · range=$START-$END max=$MAX pace=${PACE}s dir=$DIR" >> "$LOG"

cd "$DIR"
exec python3 -u -c "
import sys, time, sqlite3, os
sys.path.insert(0, '/root/wc/workspace/skills')

# Import batch summarizer
from chronicler_batch import summarize_batch, KERNEL_DB

start_id = $START
end_id = $END
max_summaries = $MAX
pace = $PACE
batch_size = int(os.environ.get('BATCH_SIZE', '5'))

conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
todo = [r[0] for r in conn.execute(
    'SELECT id FROM episodes_v2 WHERE id BETWEEN ? AND ? '
    'AND id NOT IN (SELECT episode_v2_id FROM episode_summaries) '
    'ORDER BY id ASC',
    (start_id, end_id)
).fetchall()]
conn.close()

print(f'SLOT ${SLOT} R${ROTATION} [BATCH={batch_size}] · range={start_id}-{end_id} · todo={len(todo)} max={max_summaries}', flush=True)
done = 0
fails = 0
consec_fails = 0
exit_reason = 'unknown'

idx = 0
while idx < len(todo) and done < max_summaries:
    batch = todo[idx:idx + batch_size]
    if not batch:
        break
    try:
        result = summarize_batch(batch)
        ok = result.get('ok', [])
        bad = result.get('fail', [])
        if ok:
            done += len(ok)
            consec_fails = 0
            print(f'  batch={batch} · OK={len(ok)} FAIL={len(bad)} · done={done}/{max_summaries}', flush=True)
        else:
            fails += len(batch)
            consec_fails += 1
            print(f'  batch={batch} · ALL FAIL · consec={consec_fails} · reason={result.get(\"reason\")}', flush=True)
        if consec_fails >= 3:
            exit_reason = 'cap_hit'
            print(f'SLOT ${SLOT} R${ROTATION} · 3 consec batch-fails · cap hit', flush=True)
            break
        idx += batch_size
        time.sleep(pace)
    except KeyboardInterrupt:
        exit_reason = 'interrupted'
        break
    except Exception as e:
        fails += len(batch)
        consec_fails += 1
        print(f'  batch={batch} · EXC {type(e).__name__}: {e}', flush=True)
        time.sleep(pace * 2)
        idx += batch_size
else:
    if done >= max_summaries:
        exit_reason = 'rotation_complete'
    elif idx >= len(todo):
        exit_reason = 'range_exhausted'

print(f'FINAL · SLOT ${SLOT} R${ROTATION} · done={done} fails={fails} exit={exit_reason}', flush=True)

import json
marker = {
    'slot': '${SLOT}',
    'rotation': ${ROTATION},
    'done': done,
    'fails': fails,
    'exit_reason': exit_reason,
    'finished_at': time.time(),
    'range_start': start_id,
    'range_end': end_id,
    'mode': 'BATCH',
    'batch_size': batch_size,
}
with open(f'/tmp/chronicler_slot_${LOWER}_r${ROTATION}.exit', 'w') as f:
    json.dump(marker, f)
" >> "$LOG" 2>&1
