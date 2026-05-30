#!/usr/bin/env bash
# L1 FURROW CONTINUOUS DAEMON · always-on · polls every 60s
# Calls chunk_layer2a_minimal every cycle so episodes_v2 STAYS CAUGHT UP to L0.
# This is what should have been doing the whole time so the current memory
# (right-edge of the visual) is always fresh.
# Per Ricky 2026-05-30 20:42 UTC · "current memory should always be up to date."
set -u
DIR=/root/.furrow_continuous
mkdir -p "$DIR"
touch "$DIR/CLAUDE.md"
cd "$DIR"
LOG=/tmp/furrow_continuous.log
echo "$(date -Iseconds) · FURROW CONTINUOUS DAEMON START" >> "$LOG"
export PYTHONPATH="/root/wc/workspace/skills:${PYTHONPATH:-}"
exec python3 -u <<'PY' >> "$LOG" 2>&1
import sys, time, os, sqlite3
sys.path.insert(0, '/root/wc/workspace/skills')
os.environ['WAVE_WORKER_DIR'] = '/root/.furrow_continuous'
os.environ['WAVE_WORKER_NAME'] = 'FURROW_CONTINUOUS'

KERNEL_SRC = '/root/wc/workspace/skills/continuity_kernel.py'
_NS = {}
exec(open(KERNEL_SRC).read().split('if __name__')[0], _NS)
chunk_layer2a_minimal = _NS['chunk_layer2a_minimal']
KERNEL_DB = _NS['KERNEL_DB']

print('Daemon started · loop forever · poll every 60s', flush=True)
consec_fail = 0
tick = 0
while True:
    tick += 1
    try:
        # Process up to 5 batches per tick · keeps now-edge tight
        for _ in range(5):
            ne, ned = chunk_layer2a_minimal(batch_size=20, agent='CCODE')
            if ne == 0:
                break
            consec_fail = 0
            print(f'tick={tick} +{ne}ev +{ned}ep', flush=True)
            time.sleep(2)
    except Exception as e:
        consec_fail += 1
        print(f'tick={tick} EXC {type(e).__name__}: {e}', flush=True)
        if consec_fail >= 10:
            print('STOPPING · 10 consec exceptions · likely cap-hit · sleeping 30 min', flush=True)
            time.sleep(1800)
            consec_fail = 0
    # 60s between polls · always-on but cheap
    time.sleep(60)
PY
