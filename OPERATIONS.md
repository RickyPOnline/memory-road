# Memory Road · Operations Manual

Day-to-day · pause/resume · troubleshooting.

---

## The control script

```bash
bash bin/memory_road_control.sh status   # see what's alive + progress
bash bin/memory_road_control.sh pause    # stop rotator · workers finish cleanly
bash bin/memory_road_control.sh resume   # relaunch from where left off
```

---

## Daily ops

Once installed · Memory Road runs autonomously. Day-to-day you don't need to do anything. The substrate captures · the snow plows summarize · HUNTSMAN flags · WATCHER ticks · hooks inject.

But here are the things you might want to do ·

### Check progress

```bash
bash bin/memory_road_control.sh status
```

Shows · substrate health · worker count · L3 summaries written/missing/last hour · HUNTSMAN flags · cluster count · packet freshness.

### Pre-Anthropic-Max-window-reset routine

When your Anthropic Max bucket is about to reset (typically rolling 5-hour window or daily 5:30pm UTC pattern) · you may want to PAUSE the snow plows so the freshly-recharged bucket goes to MAIN agent work, not backlog processing.

```bash
# Before the reset
bash bin/memory_road_control.sh pause

# ... do your priority work in main the agent session ...
# ... use the full window for the important stuff ...

# After the reset · plows resume
bash bin/memory_road_control.sh resume
```

Per the **never-kill-progress doctrine** · PAUSE never aborts in-flight workers. Each worker finishes its current 50-summary rotation naturally · then the manager stops. Zero lost progress.

### Force a HUNTSMAN re-sweep (find new unfinished items NOW)

```bash
python3 bin/huntsman.py --report --top 30
```

Hourly cron already does this · but if you just landed major doctrines or finished work, manual re-sweep is fine.

### Force a CARTOGRAPHER re-cluster (after big L3 growth)

```bash
python3 bin/cartographer.py --window-days 30 --max 5000
```

Re-clusters all recent summaries. Idempotent · safe to re-run.

### Propose new doctrines (run MINER+SMITH)

```bash
python3 bin/miner_smith.py --window-days 14 --max 200 --report
# Review candidate_doctrines table · LOCK strong ones · kill weak ones
sqlite3 /var/lib/memory_road/continuity_kernel.db "
  SELECT slug, title, smith_verdict, smith_reasoning
  FROM candidate_doctrines
  WHERE status='ready_to_lock'
  ORDER BY created_at DESC;
"
```

Strong candidates that survive SMITH validation are ready for operator LOCK · move them to `~/.claude/projects/-root/memory/` as `feedback_<slug>_LOCKED.md`.

---

## Troubleshooting

### Substrate not capturing events

```bash
# Status
systemctl status continuity-kernel

# Logs
journalctl -u continuity-kernel -n 100

# Re-fire
sudo systemctl restart continuity-kernel

# Check tail offset · is it advancing?
sqlite3 /var/lib/memory_road/continuity_kernel.db "SELECT value FROM kernel_state WHERE key='last_offset';"
# Run this twice with a 30s gap · should grow
```

If `last_offset` is stuck · the substrate may have a stale session pointer. Try ·

```bash
sqlite3 /var/lib/memory_road/continuity_kernel.db "DELETE FROM kernel_state WHERE key='active_session';"
sudo systemctl restart continuity-kernel
# Substrate will re-discover the newest session
```

### Workers all dying with consec-5-fail

This is the Anthropic Max bucket cap. Normal behavior · the circuit breaker is working as designed. Wait for window reset or run `bash bin/memory_road_control.sh status` periodically. The watchdog auto-relaunches when the window reopens.

### Forward sweeper not picking up new episodes

```bash
# Check watermark
cat /tmp/chronicler_forward_sweeper.watermark

# Log
tail -50 /tmp/chronicler_forward_sweeper.log

# If watermark is stale or sweeper is stopped · re-fire
pkill -f chronicler_forward_sweeper
setsid nohup bash bin/chronicler_forward_sweeper.sh </dev/null >/var/log/memory_road/forward_sweeper.log 2>&1 &
```

### Cortex packet stale (older than 10 min)

L5 WATCHER is part of the substrate. If the packet is stale ·

```bash
# Force a tick
sqlite3 /var/lib/memory_road/continuity_kernel.db ".tables" > /dev/null
# Restart substrate
sudo systemctl restart continuity-kernel
# Wait 90s · packet should refresh
ls -la $HOME/.claude/projects/<project-id>/memory/project_continuity_state.md
```

### Hook not injecting (agent says "no context")

```bash
# Is hook file present?
ls -la ~/.claude/hooks/inject_continuity_packet.sh
chmod +x ~/.claude/hooks/inject_continuity_packet.sh

# Is hook registered in settings.json?
cat ~/.claude/settings.json | python3 -m json.tool | grep -A3 UserPromptSubmit

# Is hook firing?
tail -f /tmp/inject_continuity_packet.log
# Send a test prompt · should log a new line
```

### JSONL corruption (529 cascade)

If a 529 cascade poisons the Claude Code transcript JSONL ·

```bash
# Check detector daemon status
systemctl status wave-jsonl-detector

# Manual surgery (last resort) · truncate to last clean msg_ line
# See doctrines/feedback_stop_loop_on_529_corruption_LOCKED.md for the full recipe
```

### Database getting big

```bash
# Check size
ls -lh /var/lib/memory_road/continuity_kernel.db

# Vacuum (compact)
sqlite3 /var/lib/memory_road/continuity_kernel.db "VACUUM;"

# Optional · prune raw events older than 90 days (episodes_v2 retains pointers)
sqlite3 /var/lib/memory_road/continuity_kernel.db "
  DELETE FROM events WHERE ts < strftime('%s','now') - 90*86400;
  VACUUM;
"
# Be careful · this loses raw recall · but episode summaries persist
```

---

## Monitoring (long-running)

```bash
# Quick health check (add to cron / Telegram bot / Slack)
bash bin/memory_road_control.sh status | head -30

# Episodes added per day (trend)
sqlite3 /var/lib/memory_road/continuity_kernel.db "
  SELECT date(created_at, 'unixepoch') AS day, COUNT(*)
  FROM episodes_v2
  GROUP BY day
  ORDER BY day DESC
  LIMIT 14;
"

# Summary throughput per hour
sqlite3 /var/lib/memory_road/continuity_kernel.db "
  SELECT datetime(written_at, 'unixepoch', '+0 hours') AS hour, COUNT(*)
  FROM episode_summaries
  WHERE written_at > strftime('%s','now') - 7*86400
  GROUP BY substr(hour, 1, 13)
  ORDER BY hour DESC
  LIMIT 24;
"
```

---

## Common mistakes (and how to avoid)

### "I let the kernel run for a week then realized L3 was at 5% done"

Don't forget to fire the rotator. The substrate captures forever · but comprehension needs workers. Run `memory_road_control.sh status` weekly to confirm L3 is keeping up.

### "I deleted the SQLite DB to start fresh"

That deletes your captured memory. Never do this unless you're SURE you don't want the history. Memory Road's substrate is additive-only · old data doesn't hurt anything.

### "I edited $HOME/CLAUDE.md and workers still load the old version"

Workers don't load $HOME/CLAUDE.md (blank-slate doctrine). They use an empty stub in their per-worker dir. $HOME/CLAUDE.md is for the main agent only.

### "Workers are eating my Anthropic Max bucket faster than I want"

Reduce `BATCH_SIZE` (default 5) · or reduce slot count from 4 to 2 · or pause during peak hours ·

```bash
# Pause during 9am-5pm
0 9 * * 1-5 bash $MR/bin/memory_road_control.sh pause
0 17 * * 1-5 bash $MR/bin/memory_road_control.sh resume
```

---

## When things genuinely break

1. **Always preserve the SQLite DB** · your captured memory is sacred
2. **Restart the substrate** · most issues clear with a systemctl restart
3. **Re-run failed comprehension** · workers are idempotent · re-fire whatever stopped
4. **Check the doctrine library** · `doctrines/` has scar tissue from real production failures · the fix may already be documented
5. **Worst case** · re-install. Substrate persists. Comprehension layers re-build from substrate.

---

## See also

- **bin/memory_road_control.sh** · the actual pause/resume/status script
- **doctrines/feedback_stop_loop_on_529_corruption_LOCKED.md** · 529 cascade recovery
- **doctrines/feedback_never_kill_progress_adapt_at_transitions_LOCKED.md** · why PAUSE never kills mid-flight
- **examples/smoke_test.sh** · full-stack health check
