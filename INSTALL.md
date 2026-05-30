# Memory Road · Drop-in Install

Drop-in install · canonical order · each step builds on the previous. Comprehension layers (chunking, summarization, clustering) fill in over time at the pace of your Anthropic Max bucket · the substrate captures events from second zero.

---

## Prerequisites

- Linux (Ubuntu 22.04+ tested · macOS / WSL with adaptation)
- Python 3.10+
- sqlite3 (`apt install sqlite3`)
- systemd (for L0 substrate · alternative: launchd / supervisor / cron)
- Claude Code CLI (`claude` in PATH)
- ~1GB free disk (for the SQLite DB · grows ~50MB/month)
- Optional · `sentence-transformers` Python package for CARTOGRAPHER (`pip install sentence-transformers`)

---

## Step 1 · Clone + place

```bash
# Where to install (default · /opt/memory_road · adjust as needed)
export MR=/opt/memory_road
sudo mkdir -p $MR
sudo cp -r bin/ doctrines/ hooks/ schema/ setup/ examples/ $MR/
sudo chmod +x $MR/bin/*.sh $MR/hooks/*.sh
```

---

## Step 2 · FOUNDATION (turn on substrate)

```bash
# Init the SQLite DB
sudo mkdir -p /var/lib/memory_road /var/log/memory_road
sudo sqlite3 /var/lib/memory_road/continuity_kernel.db < $MR/schema/kernel_tables.sql

# Install systemd unit
sudo cp $MR/setup/systemd/continuity-kernel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now continuity-kernel.service

# Verify
sudo systemctl is-active continuity-kernel   # → active
sqlite3 /var/lib/memory_road/continuity_kernel.db ".tables"
# → events  episodes_v2  episode_summaries  open_loops  ... etc
```

After Step 2 · **your agent's memory is being captured forever**. Events flow into the substrate. Even if you stop here · zero LLM cost · zero rate limits · indestructible recording.

---

## Step 3 · FORWARD MEMORY (now-edge stays clean)

```bash
# Fire the forward sweeper detached
sudo setsid nohup bash $MR/bin/chronicler_forward_sweeper.sh \
  </dev/null >/var/log/memory_road/forward_sweeper.log 2>&1 &

# Verify
ps -ef | grep chronicler_forward_sweeper | grep -v grep
tail -f /var/log/memory_road/forward_sweeper.log
```

After Step 3 · new episodes (anything Wave does TODAY) get summarized within 5 minutes. The now-edge of memory stays current automatically.

---

## Step 4 · BACKWARD BACKFILL (snow plow the historical backlog)

```bash
# Fire the rotator manager (4-staggered batch workers)
sudo setsid nohup bash $MR/bin/chronicler_rotator_manager.sh \
  </dev/null >/var/log/memory_road/rotator.log 2>&1 &

# Verify
ps -ef | grep chronicler_rotator | grep -v grep
tail -f /var/log/memory_road/rotator.log
```

After Step 4 · historical episodes get summaries · 4 parallel workers · recent-first · ~15-25x throughput vs naive. Resumable at any cap-hit.

---

## Step 5 · FORCE MEMORY USE (hook installation)

```bash
# Copy hooks
mkdir -p ~/.claude/hooks
cp $MR/hooks/inject_continuity_packet.sh ~/.claude/hooks/
cp $MR/hooks/force_memory_use.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh

# Configure settings.json · add hook entries
cat $MR/setup/settings.json.example
# Merge the "hooks" block into ~/.claude/settings.json manually OR ·
python3 $MR/setup/merge_settings.py
```

Restart Claude Code · the next user prompt will trigger the hooks · the agent receives the cortex packet + memory-use reminder before every turn.

---

## Step 6 · HIGHER LAYERS (HUNTSMAN · CARTOGRAPHER · MINER+SMITH)

### HUNTSMAN · hourly cron · always-on

```bash
sudo cp $MR/setup/cron/huntsman_hourly /etc/cron.d/huntsman_hourly
# Initial sweep
sudo python3 $MR/bin/huntsman.py --report --top 20
```

### CARTOGRAPHER · weekly (or on-demand)

```bash
# Install sentence-transformers if you haven't
pip install sentence-transformers

# Cluster recent 30 days
python3 $MR/bin/cartographer.py --window-days 30 --max 2000

# Add to weekly cron
echo "0 6 * * 0 root python3 $MR/bin/cartographer.py --window-days 30" \
  | sudo tee /etc/cron.d/cartographer_weekly
```

### MINER+SMITH · on-demand when L3 ≥80% recent

```bash
python3 $MR/bin/miner_smith.py --window-days 14 --max 200 --report
# Review candidate_doctrines table · LOCK strong ones · kill weak ones
```

---

## Step 7 · Verify the whole stack

```bash
bash $MR/examples/smoke_test.sh
```

Expected output ·
```
✅ L0 substrate · active
✅ L1 episodes · N chunked
✅ L3 summaries · M written
✅ L5 WATCHER · packet fresh (Xs)
✅ L12 HUNTSMAN · Y flags open
✅ Hooks · injected on next prompt
=== SMOKE TEST PASS ===
```

---

## Step 8 · Verify it survives `/compact`

In Claude Code ·
1. Have a conversation that builds context
2. Run `/compact`
3. Type a follow-up referencing earlier conversation
4. Agent should reference the cortex packet (proving forced injection) and recall via `/wmr query` if needed

If the agent says "I don't have context from earlier" · the hooks aren't firing. Re-check `~/.claude/settings.json` registration.

---

## Path adaptation

The default paths assume Wave's VPS layout. For your install, adjust ·

| Default | Adapt to |
|---|---|
| `${MEMORY_ROAD_DB:-$HOME/.memory_road/continuity_kernel.db}` | `/var/lib/memory_road/continuity_kernel.db` (or wherever) |
| `$MEMORY_ROAD_ROOT/bin/continuity_kernel.py` | `/opt/memory_road/bin/continuity_kernel.py` |
| `$HOME/.claude/projects/<project-id>/memory/` | `~/.claude/projects/<your-project>/memory/` |
| `$HOME/.memory_road/runtime/ccode_telegram_outbox.txt` | (optional · Telegram bridge) |

Each script has the path as a constant at the top · search-and-replace once.

---

## Uninstall

```bash
sudo systemctl disable --now continuity-kernel.service
sudo rm /etc/systemd/system/continuity-kernel.service
sudo rm /etc/cron.d/huntsman_hourly
pkill -f chronicler_
rm -rf ~/.claude/hooks/inject_continuity_packet.sh ~/.claude/hooks/force_memory_use.sh
# Edit ~/.claude/settings.json · remove the hooks block
# Keep /var/lib/memory_road/ · that's your captured memory · don't delete unless intentional
```

The SQLite DB is your captured memory · keep it even after uninstall. Re-install later and pick up where you left off.
