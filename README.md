# Memory Road · Quickstart

**Persistent memory for Claude Code · drop-in · 5-minute install.**

> Built by [Ricky Parker](https://github.com/RickyPOnline) with Wave (his Claude Code agent) · 2026-05-30. The substrate captures every event forever · LLM-free · indestructible. Comprehension layers extract meaning on top. Snow plow workers run in parallel from RIGHT-NOW backwards. **15-25x throughput vs naive single-fire summarization.**

---

## The 60-second pitch

Stateless agents are dumb. Every `/compact` half-forgets. Every new session re-learns from scratch. Memory Road gives any Claude Code agent ·

- A **forever-running SQLite substrate** that captures every event · cannot be rate-limited · cannot be killed by a 529
- A **fleet of named worker agents** (FURROW · CHRONICLER · HUNTSMAN · CARTOGRAPHER · MINER · SMITH · WATCHER · MENDER · etc.) that extract structured meaning over time
- A **UserPromptSubmit hook** that injects relevant memory on EVERY user prompt · the agent CANNOT forget to use it
- **Snow plow workers** that stack parallel from right-now backwards · each one cheaper than the last (blank slate + batch-5 + strip walk-up · 15-25x stacked)
- **Pause / Resume** so when your subscription window is about to reset you can save your bucket for main agent work

---

## Install (canonical order · do these top-to-bottom)

```bash
# 1. Clone
git clone https://github.com/RickyPOnline/memory-road.git
cd memory-road

# 2. FOUNDATION · the substrate (always-on systemd service)
sudo bash setup/install_substrate.sh

# 3. FORWARD MEMORY · now-edge stays clean
bash setup/install_forward_sweeper.sh

# 4. BACKWARD BACKFILL · plow historical episodes
bash setup/install_rotator.sh

# 5. FORCE MEMORY USE · agent CANNOT skip memory
bash setup/install_hooks.sh

# 6. HIGHER LAYERS (optional · fire as L3 grows)
bash setup/install_huntsman_cron.sh
python3 bin/cartographer.py --window-days 30   # one-shot
python3 bin/miner_smith.py --window-days 14   # one-shot
```

5 minutes later · your Claude Code agent has persistent memory across sessions, /compacts, model upgrades, and crashes.

---

## Verify it's working

```bash
# Substrate alive?
systemctl is-active continuity-kernel   # active

# Events captured?
sqlite3 /var/lib/memory_road/continuity_kernel.db "SELECT COUNT(*) FROM events;"

# Episodes chunked?
sqlite3 /var/lib/memory_road/continuity_kernel.db "SELECT COUNT(*) FROM episodes_v2;"

# Summaries written?
sqlite3 /var/lib/memory_road/continuity_kernel.db "SELECT COUNT(*) FROM episode_summaries;"

# HUNTSMAN flagging unfinished?
sqlite3 /var/lib/memory_road/continuity_kernel.db "SELECT COUNT(*) FROM huntsman_flags WHERE status='open';"

# Cortex packet fresh?
ls -la ~/.claude/projects/*/memory/project_continuity_state.md
```

---

## Use it

In any Claude Code session ·

```
# The hook auto-injects relevant memory on every prompt · just start typing
"What did I decide last week about the auth flow?"
# → agent reads cortex packet + queries /wmr · answers from memory

# Or explicit recall
/wmr query "auth flow decisions"
# → returns top-K most relevant memory files

# Or check unfinished work
sqlite3 /var/lib/memory_road/continuity_kernel.db \
  "SELECT description FROM huntsman_flags WHERE status='open' LIMIT 20;"
```

---

## Pause before a token-window reset

```bash
# Before Anthropic Max window resets · pause the snow plows
bash bin/memory_road_control.sh pause

# Do your priority work in the main agent · use the full window
# ...

# After reset · resume the plows from where they stopped
bash bin/memory_road_control.sh resume
```

No work is lost · the rotator picks up the next slab cleanly. Per the **never-kill-progress doctrine** · workers finish their current rotation naturally before the manager stops.

---

## The deep read

Read **SKILL.md** for the comprehensive bible · architecture · doctrines · why every choice was made.

---

## License · MIT

Use it · fork it · improve it. Built with the philosophy ·

> *"Never ask the primary agent to be the sole author of its own memory."*
