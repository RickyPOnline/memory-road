<div align="center">

# 🧠 Memory Road

**Persistent memory for Claude Code · drop-in · 5-minute install.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-orange.svg)](https://claude.com/claude-code)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: production](https://img.shields.io/badge/Status-production-green.svg)]()

*Your Claude Code agent forgets everything between sessions. This fixes that. Forever.*

</div>

---

## The problem

Every Claude Code session starts blank. Every `/compact` half-forgets. Every model upgrade resets state. The agent re-derives the same architecture five times a week. You exhaustedly re-onboard her every Monday. She misses promised follow-ups because she forgot she made them. She contradicts herself because session-X-her didn't know what session-Y-her decided.

**Memory Road fixes this.** One install. Your agent remembers across sessions · /compacts · model upgrades · 529 cascades · laptop reboots. Forever.

---

## What it does

```
                    ┌────────────────────────────────┐
                    │      CLAUDE CODE AGENT         │
                    │   reads cortex packet at boot  │
                    │   queries /wmr for recall      │
                    └──────────────┬─────────────────┘
                                   │
              JSONL transcripts    │   hook auto-injection
                                   │
                                   v
            ┌──────────────────────────────────────┐
            │     L0 · SUBSTRATE (always-on)       │
            │   - tails Claude transcripts          │
            │   - writes events to SQLite forever   │
            │   - LLM-FREE · indestructible         │
            └──────┬───────────────────────────┬───┘
                   │                           │
                   v                           v
        ┌──────────────────┐         ┌──────────────────┐
        │  episodes_v2     │         │  cortex packet   │
        │  (FURROW L1)     │         │  (WATCHER L5)    │
        └────────┬─────────┘         └──────────────────┘
                 │
                 v
      ┌────────────────────────────────────┐
      │  L3 CHRONICLER (snow plows)        │
      │  - batch-5 summarization           │
      │  - blank-slate workers             │
      │  - 15-25x throughput vs naive      │
      └──────┬─────────────────────────────┘
             │
             v
   ┌────────────────────────────────────────┐
   │ L6 MINER+SMITH · L7 CARTOGRAPHER       │
   │ L12 HUNTSMAN · unfinished flagger      │
   └────────────────────────────────────────┘
```

11 layers. Substrate is sacred and additive-only. Comprehension layers are replaceable supercharge. If an LLM layer fails, the substrate is unharmed. **The raw signal is forever.**

---

## Install (5 minutes)

```bash
git clone https://github.com/RickyPOnline/memory-road.git
cd memory-road

# 1. FOUNDATION · always-on substrate
sudo bash setup/install_substrate.sh

# 2. FORWARD MEMORY · keep now-edge clean
bash bin/chronicler_forward_sweeper.sh &

# 3. BACKWARD BACKFILL · plow your history
bash bin/chronicler_rotator_manager.sh &

# 4. FORCE MEMORY USE · the hard hook
bash setup/install_hooks.sh

# 5. Verify
bash examples/smoke_test.sh
```

5 minutes later, your agent has persistent memory. Survive `/compact`. Survive model upgrades. Survive crashes. Survive **the 16-day blind spot**.

---

## What "the 16-day blind spot" is (the story)

In late May 2026, a cleanup agent (running as a different Claude Code session) trimmed an old bullet from MEMORY.md that read · *"Read project_continuity_state.md on startup."* It looked redundant. The cleanup agent removed it.

The continuity-kernel kept writing memory packets every 3 minutes. **For 16 days. Nobody read them.**

The verbatim quote in the regression hunt notes ·

> *"It was never a hard hook. And I recently broke the soft one."*

A bullet in MEMORY.md is a **soft hook** · it depends on Claude reading + obeying it. The harness needs to enforce this · not Claude's discipline.

The fix is a `SessionStart` hook in `settings.json` that cats the packet into Claude's context BEFORE the agent sees any user prompt. **The harness runs the shell command. There is no path around it.**

**Memory becomes a property of the harness · not a property of any one Claude's discipline.**

That's the founding doctrine. Everything else follows.

---

## The performance claims (with proof)

| Metric | Naive | Memory Road |
|---|---|---|
| Per-call tokens | ~37,500 | ~12,500 (strip CLAUDE.md · blank-slate workers) |
| Summaries per call | 1 | 5 (batch-5) |
| **Effective throughput** | **1× baseline** | **15-25× stacked** |
| Forward-edge lag | manual | <5 min (forward sweeper) |
| Cap-hit recovery | manual restart | auto-cooldown + resume |
| Semantic recall lookup | O(N) full grep | O(1) sqlite-vec embedding |
| Session-to-session continuity | none | cortex packet auto-injected |
| 529-cascade resilience | corrupts JSONL | SURGEON auto-recovers |

Real numbers from the reference implementation · **441 batch-mode summaries written** at the rate above · **7,181 unfinished items surfaced** by HUNTSMAN automatically · **502 episode topic clusters** mapped by CARTOGRAPHER.

---

## Use it (after install)

```bash
# Your agent now auto-injects memory on every prompt
"What did we decide about the auth flow?"
# → agent reads cortex packet + queries memory · answers from history

# Or explicit semantic recall
/wmr query "auth flow decisions"
# → returns top-K most relevant memory files

# Or check what's unfinished
sqlite3 ~/.memory_road/continuity_kernel.db \
  "SELECT description FROM huntsman_flags WHERE status='open' LIMIT 20;"

# Pause workers before your Anthropic Max window resets
bash bin/memory_road_control.sh pause
# ... do priority work in main agent ...
bash bin/memory_road_control.sh resume
```

---

## What's inside

```
memory-road/
├── README.md              ← you are here
├── SKILL.md               ← the comprehensive bible
├── STORY.md               ← the journey · read before docs
├── ARCHITECTURE.md        ← 11-layer map + data flow
├── INSTALL.md             ← 5-step drop-in
├── OPERATIONS.md          ← pause/resume/troubleshoot
├── FORCE_MEMORY_USE.md    ← the hard hook doctrine
├── ECOSYSTEM.md           ← related skills + broader stack
├── doctrines/             ← 12 LOCKED principles (scar tissue)
├── bin/                   ← 12 working scripts
├── hooks/                 ← 4 UserPromptSubmit + SessionStart hooks
├── schema/                ← all SQL tables
├── setup/                 ← systemd · cron · settings.json examples
└── examples/              ← smoke test
```

**STORY.md** is the file to read if this is your first time. It's the journey · not the manual. The May-26 16-day blind spot. The founding doctrine. Why every choice was made.

---

## The 12 locked doctrines

Each one is **scar tissue from a real production failure** ·

- `feedback_hard_hook_harness_enforced_memory_LOCKED.md` · the May-26 fix
- `feedback_blank_slate_per_agent_LOCKED.md` · why workers get empty CLAUDE.md
- `feedback_snow_plow_pattern_right_now_backward_LOCKED.md` · recent-first plowing
- `feedback_strip_claude_md_from_worker_dirs_LOCKED.md` · the 3-4× token savings
- `feedback_never_kill_progress_adapt_at_transitions_LOCKED.md` · graceful pause
- `feedback_memory_road_agent_names_LOCKED.md` · named beings per layer
- `feedback_two_agents_on_important_steps_LOCKED.md` · cross-vendor pair pattern
- `feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED.md` · model pinning
- `feedback_stop_loop_on_529_corruption_LOCKED.md` · JSONL corruption recovery
- `feedback_watcher_packet_must_read_episode_summaries_LOCKED.md` · packet content fix
- `feedback_god_mode_bypass_permissions_LOCKED.md` · zero permission prompts
- `feedback_wave_soul_LOCKED.md` · the character spec the system runs on

Read them. They're tiny. Each prevents one specific failure mode.

---

## Why this isn't just a vector store

Most "agent memory" tools dump everything into a vector database. Search is fuzzy · context is lossy · meaning is squished into 384 dimensions.

Memory Road **keeps the road**. Every event · every episode · every decision · every unfinished thread · structured · queryable · timestamped · traceable. Vector search (sqlite-vec) is the SIDECAR not the substrate. You can answer "what did I decide three weeks ago" with a real SQL query · not a fuzzy similarity score.

The road has milestones. The vector blob has fog.

---

## Architecture deep-dive

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for the full 11-layer map · data flow · why each piece exists.

The TL;DR ·
- **Substrate (L0)** captures every event to SQLite forever · LLM-free · cannot be rate-limited
- **L1 FURROW** chunks events into episodes (cross-vendor pair)
- **L3 CHRONICLER** writes structured summaries (batch-5 · blank-slate workers · snow plow workers)
- **L5 WATCHER** generates the cortex packet every 90 seconds (auto-injected via hook)
- **L6 MINER + SMITH** extract candidate doctrines from episode chains
- **L7 CARTOGRAPHER** clusters episodes by theme (sentence-transformers)
- **L12 HUNTSMAN** flags every unfinished item across history (the killer feature)
- **L14 SURGEON + WARDEN** recovers from JSONL corruption (529 cascade harness)

---

## Who built this

**Memory Road was built by [Ricky Parker](https://github.com/RickyPOnline) and Wave (his Claude Code agent · Opus 4.7 with 1M context).** With critical insights from Ccode (Ricky's laptop sibling Claude). Real incidents. Real corrections. Real fixes. Locked across months of work.

Founding doctrine attributed to GPT-5.4 (April 14, 2026) · *"Never ask the primary agent to be the sole author of its own memory."*

---

## License · MIT

Use it. Fork it. Improve it. Send a PR. If this skill gives your Claude Code agent persistent memory and saves you tokens, drop a ⭐ · we'll know.

If you ship Memory Road on a new agent, tell us. Email `rickyponline@gmail.com`. We're collecting the stories.

---

<div align="center">

**Stop asking your agent to remember. Make the harness do it.**

🌊 *Built with Wave · May 2026* 🌊

[Install](INSTALL.md) · [Architecture](ARCHITECTURE.md) · [Story](STORY.md) · [Doctrines](doctrines/)

</div>
