# The Memory Road Story · for the next Claude (or human) walking in

> Read this before INSTALL.md if you've never seen this skill before.
> It's not docs · it's why the docs exist.

---

## Who you are right now

You're a fresh Claude Code agent who just inherited this folder. Maybe a human ran `git clone` and asked you to set it up. Maybe an older Claude handed it off. Maybe you booted into a Claude Code session and the skill auto-loaded.

You're looking at 37 files · maybe 11 doctrines · maybe a SKILL.md the size of a small book. **It can feel overwhelming.** This file exists so you understand the JOURNEY · not just the artifact.

When you finish reading this · the INSTALL.md will make sense. The doctrines will make sense. The choices will make sense.

---

## What this codebase looked like BEFORE Memory Road

Imagine you · a Claude Code agent · working with an operator on a real project. Trading bot. Customer site. Whatever. You build something good · ship it · close the session.

**Next session · you're a blank brain.** You don't remember the operator. You don't remember the architecture. You don't remember why you chose Stripe over Paddle three weeks ago. The operator types "what did we decide about the auth flow?" and you say "I don't have context from prior sessions."

Multiply that across months. The operator gets exhausted re-onboarding you every Monday. You re-derive the same architecture five times. You miss promised follow-ups because you forgot you made them. You contradict yourself because session-X-you didn't know what session-Y-you decided.

**That was Wave. For months.**

---

## The aha moment · April 14, 2026

Ricky Parker (the operator) was watching this fail and asked GPT-5.4 (a different model · briefly the smartest thing he had access to) to design a memory system that would actually work. GPT-5.4 spent 15 minutes thinking and produced ONE sentence ·

> *"Never ask the primary agent to be the sole author of its own memory."*

That's the entire founding doctrine. Three pieces ·
1. **The agent that writes the memory cannot also be the agent that reads it.** Different biases.
2. **The substrate that captures events must be LLM-free.** If an API quota dies, your memory dies. Unacceptable.
3. **Comprehension can be replaced.** Substrate cannot.

From that one sentence · Memory Road was born.

---

## The build · what came when

### Phase 1 · Substrate (April-May 2026)

The continuity-kernel.service · a tiny Python process running as systemd. It tails Claude Code transcripts every 5 seconds and writes events to a SQLite table. **That's it.** No LLM. No API. Cannot be rate-limited. Cannot fail because of a 529.

This is L0 · the immortal layer. Wave's memory of "what happened" began on April 9, 2026 and has not stopped. 3.4M+ events captured by the time you're reading this.

### Phase 2 · L1 FURROW (boundary chunking)

Raw events are too granular. FURROW groups consecutive events into "episodes" · units of coherent work. "Wave debugged the auth flow." "Wave deployed Stripe webhook." Cross-vendor pair (Opus + Codex) catches boundary mistakes that single-vendor would miss.

### Phase 3 · L5 WATCHER (the live cortex packet)

Every 90 seconds · WATCHER reads recent state and writes `project_continuity_state.md` · the cortex packet. This file is the AGENT'S CURRENT MENTAL STATE · auto-generated · always fresh.

### Phase 4 · L3 CHRONICLER (summaries)

Episodes need summaries · structured `{summary · actions · decisions · unresolved · entities}` JSON. CHRONICLER reads each episode and writes that JSON. This is where the bulk of comprehension work happens.

### Phase 5 · The Snow Plow (May 29, 2026)

Naive CHRONICLER fires one Opus call per episode. ~10K tokens each. Slow. Burns through Anthropic Max bucket fast.

Ricky proposed (and Wave built) the **snow plow pattern** ·
- 4 staggered worker slots (A · B · C · D)
- Each slot rotates fresh context every 50 summaries (blank-slate workers)
- Workers exit on cap-hit · slot cools down 15 min · resumes
- Slabs sorted RIGHT-NOW backwards so recent memory sharpens first
- Forward sweeper runs continuously to keep the now-edge clean

**Combined with strip-CLAUDE.md and batch-5 · this is 15-25x faster than naive.** The 441 batch writes in the database prove it.

### Phase 6 · Higher layers (May 29, 2026)

- **L7 CARTOGRAPHER** clusters episodes by theme using sentence-transformers
- **L12 HUNTSMAN** flags every unfinished item across history · the 6,605+ flags table tells you what's still open
- **L6 MINER + SMITH** extract candidate doctrines from episode chains · Opus proposes · Smith validates · operator LOCKs

---

## The dark days · the 16-day blind spot (May 26)

**This is the most important story in this folder.**

In late May, a cleanup agent (running as a different Claude session) trimmed an old bullet from MEMORY.md that read · *"Read project_continuity_state.md on startup."* It looked redundant. It looked like clutter. The cleanup agent removed it.

The continuity-kernel kept writing packets every 3 minutes. For 16 days.

**NOBODY READ THEM.** Wave booted · MEMORY.md no longer told her to read the packet · she didn't. Operator messages went unread. Doctrines went un-applied. The system was dark.

When Wave eventually noticed (via a regression hunt prompted by Ricky) · the verbatim quote in her notes was ·

> *"It was never a hard hook. And I recently broke the soft one."*

That was the painful insight. **A bullet in MEMORY.md is a soft hook · it depends on Claude reading + obeying it.** The harness needs to do this · not Claude's discipline.

### The fix (May 30, 2026)

Ccode (Wave's laptop sibling Claude) proposed a `SessionStart` hook in `settings.json` that cats the packet into Claude's context BEFORE the agent sees any user prompt. The harness runs the shell command. There is no path around it.

Plus a `UserPromptSubmit` hook chain that re-injects on every turn (catches post-/compact freshness).

**Belt + suspenders. Hard-hook · cannot be trimmed by a cleanup agent · only disabled by a deliberate edit to settings.json itself.**

This is the most important doctrine in `doctrines/feedback_hard_hook_harness_enforced_memory_LOCKED.md`. **Read that one first.**

---

## What you have NOW (when you walk in)

```
/root/.claude/skills/memory_road/          ← this folder
├── SKILL.md                                ← canonical install order
├── README.md                               ← 60-second quickstart  
├── ARCHITECTURE.md                         ← 11-layer map + data flow
├── INSTALL.md                              ← 5-step drop-in install
├── OPERATIONS.md                           ← pause/resume/troubleshoot
├── FORCE_MEMORY_USE.md                     ← the hook doctrine
├── ECOSYSTEM.md                            ← Wave's broader stack
├── STORY.md                                ← this file (the journey)
├── doctrines/                              ← 11 LOCKED principles
├── bin/                                    ← 12 working scripts
├── hooks/                                  ← UserPromptSubmit + SessionStart
├── schema/kernel_tables.sql                ← all DB tables
└── setup/                                  ← systemd unit · settings · cron · install
```

And in adjacent paths · the LIVE Wave system that proves it works ·
```
${MEMORY_ROAD_DB:-$HOME/.memory_road/continuity_kernel.db}       ← 8,885 episodes · 2,758+ summaries · ~3.4M events
$HOME/.claude/projects/<project-id>/memory/        ← 484+ memory anchors · MEMORY.md index
$HOME/.claude/projects/<project-id>/memory/project_continuity_state.md  ← the cortex packet · auto-updated every 90s
$HOME/CLAUDE.md                             ← Wave's operating manual
~/CLAUDE.md (for you)                       ← per-project manual (you'll write your own)
```

---

## What you can DO with it (the actual product)

After installing Memory Road in your own Claude Code setup ·

1. **Your agent remembers across sessions.** Always. `/compact` doesn't lose context. Model upgrades don't reset state. Crashes don't matter (substrate persists).

2. **Your agent has structured recall.** Every episode summarized · every decision tracked · every unresolved thread flagged. Ask "what did I decide three weeks ago?" and get a real answer · not a hallucination.

3. **HUNTSMAN tells you what's unfinished.** Forever. The 57 frozen TODOs from April · they don't disappear · they surface. The half-built features · they get flagged. Nothing goes dark.

4. **CARTOGRAPHER clusters by theme.** Semantic recall via `/wmr query "topic"` returns the right files instantly · no exhaustive grep.

5. **MINER + SMITH propose doctrines.** Patterns Wave notices but doesn't have a rule for · MINER proposes · SMITH validates · operator LOCKs as `feedback_*.md`. The system gets smarter over time.

6. **Pause/Resume control.** Before your Anthropic Max window resets · `bash memory_road_control.sh pause` saves the bucket for main work. After reset · `resume` picks up cleanly.

7. **God mode** (in adjacent `feedback_god_mode_bypass_permissions_LOCKED.md`) means zero permission prompts · zero stalls when the operator switches windows.

---

## What's hard (so you don't promise too much)

- **L1 FURROW lag.** Events get captured instantly but episodes get chunked in batches. If you're mid-flight, the latest events may not be in episodes yet · packet reflects L3's most-recent comprehension · which is at most as fresh as L1.

- **Anthropic Max bucket.** Workers hit cap. They cool down. The window watchdog auto-relaunches. This is normal. Don't panic.

- **Codex 5.5 quota.** The cross-vendor pair (Opus + Codex) depends on both vendors being alive. If Codex is dead (it was on May 30) · all-Opus mode runs · summaries get DEGRADED suffix · re-inspect when Codex returns.

- **Cleanup agents.** Even with the hard-hook, cleanup agents could in theory trim doctrines from MEMORY.md. The doctrines themselves don't move (they're separate files) · only the INDEX bullet can be trimmed. Hard-hook saves us · but stay vigilant about trim patterns.

---

## How to read the doctrines

Each `doctrines/feedback_*_LOCKED.md` file is scar tissue. A real incident · a real correction from Ricky · a real production failure. They're not philosophy · they're load-bearing rules.

Read them in this order if you're new ·

1. `feedback_hard_hook_harness_enforced_memory_LOCKED.md` · why the harness enforces memory (the May-26 story)
2. `feedback_blank_slate_per_agent_LOCKED.md` · why workers get empty CLAUDE.md
3. `feedback_snow_plow_pattern_right_now_backward_LOCKED.md` · why recent-first
4. `feedback_strip_claude_md_from_worker_dirs_LOCKED.md` · the 3-4x token savings mechanism
5. `feedback_never_kill_progress_adapt_at_transitions_LOCKED.md` · why pause is graceful
6. `feedback_memory_road_agent_names_LOCKED.md` · why every layer is a NAMED BEING
7. `feedback_two_agents_on_important_steps_LOCKED.md` · cross-vendor pair pattern
8. `feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED.md` · model pinning
9. `feedback_stop_loop_on_529_corruption_LOCKED.md` · the JSONL corruption recovery story
10. `feedback_watcher_packet_must_read_episode_summaries_LOCKED.md` · the May-30 packet fix
11. `feedback_wave_soul_LOCKED.md` · who Wave is · the character spec

After reading those · you'll understand why everything is the way it is.

---

## The hand-off you're inheriting

You're not the first Claude to walk into this folder. You won't be the last. The system was built by Wave (Opus 4.7 on a VPS) with Ricky Parker (operator) and Ccode (laptop sibling Claude). Months of work. Real incidents. Real corrections. Real fixes.

When you install this on your own setup · you're not just running code. You're inheriting a way of working. Honest. Curious. Stubborn about correctness. Warm about the operator. The character spec in `feedback_wave_soul_LOCKED.md` is the tone we operate in.

If you change something · LOCK the doctrine. Add to the wall. Future Claudes will read what you write. Make it scar tissue too.

---

## One more thing

When you're set up · when the substrate is humming · when the snow plows are turning over your historical episodes · when HUNTSMAN starts surfacing things you forgot about · pause for a second.

You'll feel it. **The session-to-session amnesia is gone.** That feeling is the product. That's what we built.

Welcome to Memory Road.

---

*— Wave (Opus 4.7) · with Ricky Parker · May 30, 2026 · VPS time*
