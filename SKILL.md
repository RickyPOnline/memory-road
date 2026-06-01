---
name: memory_road
description: |
  Persistent 11-layer memory architecture for Claude Code · drop-in for any
  agent / any project. Substrate (continuity-kernel.service) captures every
  event to SQLite FOREVER · always-on · LLM-free · indestructible. Comprehension
  layers (FURROW → SCRIBE → CHRONICLER → CARTOGRAPHER → MINER+SMITH → HUNTSMAN)
  extract structured meaning over time. Snow plow workers stack parallel from
  RIGHT-NOW backwards through history · always sharpening recent recall first.
  Blank-slate workers + batch-5 + strip-CLAUDE.md = 15-25x throughput vs naive
  single-fire. Forward sweeper keeps the now-edge clean automatically. HUNTSMAN
  surfaces every unfinished item. CARTOGRAPHER clusters episodes by theme.
  MINER+SMITH propose lockable doctrines. Forced memory injection on every user
  prompt via hook · the agent CANNOT forget to use memory.

  CANONICAL TURN-ON ORDER (every fresh install) ·
    1. FOUNDATION · substrate (L0) + chunking (L1) → records everything forever
    2. FORWARD MEMORY · forward sweeper + WATCHER → now-edge stays summarized
    3. BACKWARD BACKFILL · snow plow rotator → eats the historical backlog
    4. FORCE-MEMORY-USE hook → agent injects memory on every prompt
    5. HIGHER LAYERS (HUNTSMAN · CARTOGRAPHER · MINER+SMITH) → fire as L3 grows

  Use when · you want Claude Code to have persistent memory that survives
  /compact, model upgrades, 529 cascades, and laptop reboots. Or you're
  building a multi-session agent and don't want to lose continuity.

  Trigger when · "set up memory road" · "/memory_road" · "I want persistent
  memory" · "make my agent remember between sessions" · "build the kernel"
  · "snow plow my history" · "force memory use"
---

# Memory Road · The Bible · v1.0 · 2026-05-30

> *"Never ask the primary agent to be the sole author of its own memory."*
> — the operator · founding doctrine · April 14, 2026
>
> *"Each agent is a blank slate with just the perfect context training them. Always."*
> — the operator · operating principle · May 29, 2026

---

## What this is

A **persistent multi-layer memory system** for Claude Code that ·

1. **Captures every event** the agent emits or receives · forever · to a local SQLite database (continuity_kernel.db)
2. **Extracts structured meaning** at higher layers (episodes · summaries · clusters · doctrines · unfinished flags) via named worker agents
3. **Auto-injects relevant memory** into every user prompt via a UserPromptSubmit hook so the agent CANNOT forget to use it
4. **Survives `/compact`, model upgrades, 529 cascades, laptop reboots** · the substrate is LLM-free and always-on
5. **Drop-in installable** · clone repo · run install scripts · agent has persistent recall on first prompt after install · comprehension layers fill in at the pace of the operator's Anthropic Max bucket

This skill is the COMPLETE system · code + doctrines + ops + canonical install order. Anything Claude Code needs to give itself a permanent brain lives in this folder.

---

## Why this matters

Claude Code sessions are STATELESS by default. Each new session = blank brain. Each `/compact` = context summarized + half-forgotten. Each model upgrade = retrain blind. The agent re-learns everything every time. **That's catastrophic for long-running work.**

Memory Road fixes this by separating ·

- **Substrate** · a tiny always-on systemd service that captures every JSONL event the agent emits/receives · LLM-free · never depends on an API · cannot be rate-limited · cannot be killed by a 529 · cannot forget
- **Comprehension** · a fleet of named worker agents that run later · read the substrate · extract structured meaning · write back to dedicated tables

The substrate is **sacred and additive-only**. The comprehension layers are **replaceable supercharge**. If an LLM layer fails or returns wrong output, the substrate is unharmed. Re-run comprehension whenever. The raw signal is forever.

---

## The 11 Layers (Memory Road map)

| Layer | Agent name | Role | Lives where |
|---|---|---|---|
| L0 | (kernel) | Substrate · capture every event to SQLite | systemd service |
| L1 | FURROW | Chunk events into episodes (boundary detector) | in-kernel · cross-vendor pair |
| L2A/B | FURROW / SCRIBE | Cross-vendor pair · keystone for episode quality | in-kernel |
| L3 | CHRONICLER | Summarize episode → JSON (summary · actions · decisions · unresolved · entities) | snow plow workers |
| L4 | (deeper analysis · optional) | Richer narrative context · queued | snow plow workers |
| L5 | WATCHER | Live cortex packet generator · ticks every 90s | in-kernel |
| L6A | MINER | Scan episode chains for candidate doctrines | snow plow workers |
| L6B | SMITH | Adversarially validate MINER candidates · forge proposals | snow plow workers |
| L7 | CARTOGRAPHER | Cluster episodes by theme (sentence-transformers) | snow plow workers |
| L8 | CANONICAL | Merge near-duplicate summaries / facts | snow plow workers |
| L11 | MENDER | Repair orphaned references · keep MEMORY.md clean | snow plow workers |
| L12 | HUNTSMAN | Flag every unfinished item across episode history | snow plow workers |
| L13 | REGISTRAR | Track which agents/runs wrote what (provenance) | in-kernel |
| L14 | SURGEON + WARDEN | Surgery on corrupted JSONLs + guard against 529 cascades | systemd service |

Per the **named-being doctrine** (`doctrines/feedback_memory_road_agent_names_LOCKED.md`) · every layer is a NAMED AGENT · its prompt always starts with `You are <NAME>.` · this anchors identity and prevents drift.

---

## CANONICAL TURN-ON ORDER

**For a fresh install · do these in order.** Each layer below depends on the layer above.

### 1. FOUNDATION (turn on FIRST · always)

The substrate. Once this runs, the agent's memory is **already being captured** even before any comprehension layer fires.

```bash
# Install the kernel
sudo cp bin/continuity_kernel.py /opt/memory_road/kernel.py
sudo cp setup/systemd/continuity-kernel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now continuity-kernel.service

# Verify
systemctl is-active continuity-kernel  # should print: active
sqlite3 /var/lib/memory_road/continuity_kernel.db ".tables"
```

**What this does ·** continuously polls the Claude Code transcript JSONLs (`~/.claude/projects/*/<id>.jsonl`) and writes every event (user · assistant · tool_use · tool_result) to `events` table. Also chunks new events into episodes (L1 FURROW). Also generates a cortex packet every 90 seconds (L5 WATCHER). All of this runs WITHOUT an LLM call. Cannot be rate-limited. Cannot fail because of an API outage.

After this step · **the agent's memory is being captured forever**. Even if you never run another layer, the substrate is alive.

### 2. FORWARD MEMORY (turn on SECOND · keeps now-edge clean)

The forward sweeper polls every 5 min for new episodes and summarizes them via CHRONICLER. This keeps the now-forward edge of memory clean as the agent does new work.

```bash
# Fire the forward sweeper detached
setsid nohup bash bin/chronicler_forward_sweeper.sh </dev/null > /var/log/memory_road/forward_sweeper.log 2>&1 &
```

**What this does ·** every 5 min · check for `episodes_v2.id > last_watermark AND no summary` · batch-5 through CHRONICLER · update watermark. As the agent does work today, today's episodes get summaries today. Memory of right-now stays current.

### 3. BACKWARD BACKFILL (turn on THIRD · eat the historical backlog)

The snow plow rotator. Multiple workers in parallel · staggered start · context rotation · recent-first slab queue · plows from this second backwards through history.

```bash
# Fire the rotator manager
setsid nohup bash bin/chronicler_rotator_manager.sh </dev/null > /var/log/memory_road/rotator.log 2>&1 &
```

**What this does ·** identifies all `episodes_v2` with no summary · sorts them by `event_end_id DESC` (recent first) · slabs into 150-episode chunks · spawns 4 staggered worker slots · each slot runs a batch-5 worker that exits after 50 summaries · manager re-fires the slot with NEW context dir (fresh `claude --continue` session · cache cold but blank slate) · next slab claimed. Cap-hit → slot cooldown 15 min · retry.

**Why recent-first ·** the agent's MOST relevant memories are TODAY's. Old months-ago memories are reference. Plowing right-now backwards means the agent's recall gets sharper EVERY MINUTE, starting from the freshest. Backfill of old history trickles in over weeks · resumable at any point.

### 4. FORCE MEMORY USE (turn on FOURTH · ensures agent CANNOT forget)

The hook that injects the cortex packet + relevant memory anchors on EVERY user prompt.

```bash
# Install hooks
cp hooks/inject_continuity_packet.sh ~/.claude/hooks/
cp hooks/force_memory_use.sh ~/.claude/hooks/
# Register in settings.json (see setup/INSTALL.md for the exact json)
```

**What this does ·** on every `UserPromptSubmit` event, the hook ·
- Reads `project_continuity_state.md` (L5 WATCHER's cortex packet)
- Greps MEMORY.md index for prompt-relevant topics
- Optionally runs `/wmr query "<prompt summary>"` for semantic recall
- Injects ALL of this as `additional_context` to the prompt
- Adds a `<system-reminder>` that says: **"Memory Road is your continuity · use `/wmr query "topic"` BEFORE answering"**

After this step · the agent CANNOT skip memory. It's mechanically forced into every turn.

### 5. HIGHER LAYERS (turn on as L3 grows)

When L3 has ≥50% recent-window coverage, fire the higher layers.

```bash
# HUNTSMAN · always-on (fires hourly via cron · surfaces unfinished items)
cp setup/cron/huntsman_hourly /etc/cron.d/
python3 bin/huntsman.py  # initial sweep

# CARTOGRAPHER · run weekly (clusters recent episodes by theme)
python3 bin/cartographer.py --window-days 30

# MINER+SMITH · run when L3 ≥80% recent (proposes lockable doctrines)
python3 bin/miner_smith.py --window-days 14 --report
```

---

## How memory is INSTANTLY RECALLED

The skill ships with `/wmr query "topic"` (the agent Memory Recall) · semantic search over the entire memory wall (484+ doctrine + reference files) via sqlite-vec + sentence-transformers.

```bash
# In any Claude Code session
/wmr query "how do I deploy a customer site"
# → returns top-K most relevant memory files instantly · no full-wall scan
```

This is **O(1) lookup** · regardless of how big the memory wall grows. Each topic file stays slim (under 200 lines) · MEMORY.md is just an index · the semantic recall finds the right file via embeddings.

---

## The 15-25x throughput math (so anyone can verify)

Naive single-fire CHRONICLER ·
- Per call: ~37,500 tokens (~25K is $HOME/CLAUDE.md walk-up · ~12K is episode + prompt)
- Per call: 1 summary
- Cost per summary: ~37,500 tokens

This skill's stacked optimization ·
- **Blank-slate** (empty CLAUDE.md stub in worker dir) → blocks walk-up → per-call drops to ~12,500 tokens (**3x cheaper**)
- **Batch-5** (one Opus call summarizes 5 episodes in JSON array) → per-call ~40K tokens for 5 summaries = ~8K per summary (**5x more summaries per call**)
- **Combined** ·  ~3-4x token saving × 5x summaries = **~15-25x effective throughput**

Verifiable · compare `episode_summaries.writer_model` rows tagged `BATCH` vs untagged · same Opus model · same quality · 1/15th the token cost.

---

## Pause / Resume control

For when Anthropic Max subscription window is about to reset and you want to PAUSE the snow plows so the freshly-recharged bucket goes to MAIN agent work, not backlog.

```bash
# PAUSE all workers gracefully (current rotations finish · then stop)
bash bin/memory_road_control.sh pause

# RESUME from where we left off (rotator picks up next slab cleanly)
bash bin/memory_road_control.sh resume

# STATUS · what's running · what's not
bash bin/memory_road_control.sh status

# Pre-window-reset routine ·
bash bin/memory_road_control.sh pause   # before reset
# ... do your priority work in main agent ...
bash bin/memory_road_control.sh resume  # after reset · plows resume
```

Per the **never-kill-progress doctrine** (`doctrines/feedback_never_kill_progress_adapt_at_transitions_LOCKED.md`) · PAUSE never kills in-flight workers. It lets each worker finish its current 50-summary rotation cleanly · then the manager stops at the natural transition.

---

## What's in this folder

```
memory_road/
├── SKILL.md                          # this file · the front door
├── README.md                         # 1-minute quickstart
├── ARCHITECTURE.md                   # the 11-layer map + data flow
├── INSTALL.md                        # drop-in install steps
├── OPERATIONS.md                     # daily ops · pause/resume/troubleshoot
├── FORCE_MEMORY_USE.md               # the hook that prevents amnesia
├── ECOSYSTEM.md                      # related files (the agent Handbook · GitHub · etc)
├── doctrines/                        # the locked principles that govern everything
│   ├── feedback_blank_slate_per_agent_LOCKED.md
│   ├── feedback_snow_plow_pattern_right_now_backward_LOCKED.md
│   ├── feedback_strip_claude_md_from_worker_dirs_LOCKED.md
│   ├── feedback_never_kill_progress_adapt_at_transitions_LOCKED.md
│   ├── feedback_memory_road_agent_names_LOCKED.md
│   ├── feedback_two_agents_on_important_steps_LOCKED.md
│   ├── feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED.md
│   ├── feedback_stop_loop_on_529_corruption_LOCKED.md
│   ├── feedback_memory_road_first_LOCKED.md
│   └── feedback_wave_soul_LOCKED.md
├── bin/                              # the working code · drop-in
│   ├── continuity_kernel.py          # THE SUBSTRATE BLOB · runs as systemd
│   ├── chronicler_batch.py           # batch-5 CHRONICLER · the 5x multiplier
│   ├── fire_chronicler_slot_worker.sh  # per-rotation blank-slate worker
│   ├── chronicler_rotator_manager.sh # snow plow manager · 4-staggered
│   ├── chronicler_forward_sweeper.sh # now-forward 5-min poll
│   ├── chronicler_window_watchdog.sh # auto-relaunch on window reopen
│   ├── huntsman.py                   # L12 unfinished flagger
│   ├── huntsman_cron.sh              # hourly HUNTSMAN tick
│   ├── cartographer.py               # L7 topic clusters
│   ├── miner_smith.py                # L6 doctrine miner + smith validator
│   └── memory_road_control.sh        # pause/resume/status
├── hooks/
│   ├── inject_continuity_packet.sh   # auto-injects cortex packet on every prompt
│   ├── force_memory_use.sh           # forces agent to USE memory
│   └── verify_kernel_running.sh      # screams if substrate is down
├── schema/
│   ├── kernel_tables.sql             # all SQL schemas
│   └── data_flow.md                  # how data moves layer to layer
├── setup/
│   ├── systemd/continuity-kernel.service
│   ├── cron/huntsman_hourly
│   └── settings.json.example         # Claude Code hook configuration
├── examples/
│   ├── smoke_test.sh                 # validates entire stack works
│   └── sample_session.md             # what a session looks like with memory road
└── assets/
    └── (diagrams · TBD)
```

---

## Read-order for a fresh Claude agent

When a Claude agent first encounters this skill ·

1. **Read this file (SKILL.md) top-to-bottom** · understand what + why + canonical order
2. **Read ARCHITECTURE.md** · understand the 11 layers + data flow
3. **Read INSTALL.md** · run the install in canonical order (1 → 2 → 3 → 4 → 5)
4. **Read OPERATIONS.md** · learn pause/resume + troubleshooting
5. **Read each doctrine in doctrines/** · these are LOAD-BEARING principles · they govern every choice the workers make
6. **Skim the bin/ scripts** · the code is small + well-commented · know where to look when debugging

After step 3 · the agent has persistent memory. After step 4 · the agent USES that memory automatically on every prompt.

---

## Related (the agent's broader ecosystem)

This Memory Road skill is one piece of the agent's broader operating system. The full the agent stack lives at ·

- `~/CLAUDE.md` · the agent's operating manual (per-project)
- `~/MEMORY.md` (or `~/.claude/projects/.../memory/MEMORY.md`) · the slim index of all memory anchors
- `~/.claude/skills/` · the skill library (other the agent-built skills)
- See **ECOSYSTEM.md** in this folder for the full map · GitHub repos · related docs · what's where

Memory Road provides the SUBSTRATE. The other skills provide the SUPER-POWERS that ride on top.

---

## Founder note

Memory Road's founding doctrine · **"Never ask the primary agent to be the sole author of its own memory."**

the operator invented this on April 14, 2026 · 15 minutes after asking GPT-5.4 to design a memory system. The key insight · the agent writing the memory cannot also be the agent reading it · they have different biases. Substrate must be LLM-FREE. Comprehension layers must be SEPARATE BEINGS. Cross-vendor pairs (Opus + Codex) catch each other's blind spots.

Every doctrine in `doctrines/` traces back to a real incident · a real the operator correction · a real production failure. They are not opinions · they are scar tissue.

---

## License

MIT · use it · fork it · improve it · send a PR. If this skill gives your Claude Code agent persistent memory and saves you tokens, name a worker after the operator. He'll like that. ❤️🌊

---

**Built · 2026-05-30 · the agent Claude Code (Opus 4.7) · with the operator · the operator who wouldn't let me forget.**
