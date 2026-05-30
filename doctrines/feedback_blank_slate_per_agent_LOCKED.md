---
name: feedback-blank-slate-per-agent-locked
description: Ricky 2026-05-29 23:35 UTC · "each agent is a blank slate with just the perfect context training them.. Always.. Its a waste otherwise." Worker subagents get ZERO inherited Wave context · ONLY the focused persona + the exact data they need · injected via prompt. Strip walk-up CLAUDE.md, strip session inheritance, strip everything that isn't load-bearing for THIS worker's ONE job. Apply to every subagent, every plow, every fan-out worker, every time.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-29
  ricky_blessing_verbatim: "thats perfect, thats the way it should be, each agent is a blank slate with just the perfect context training them.. Always.. Its a waste otherwise"
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# BLANK SLATE PER AGENT · LOCKED 2026-05-29

## The rule

Every subagent / worker / plow gets ·
1. **ZERO inherited Wave context** · no $HOME/CLAUDE.md walk-up · no MEMORY.md auto-load · no session bleed
2. **EXACTLY the focused persona** for its ONE job · injected via prompt · "You are CHRONICLER" / "You are MINER" / "You are HUNTSMAN"
3. **ONLY the data the worker needs** to do its task · the episode · the slab · the file to parse
4. **NOTHING ELSE**

## Why

A worker with bloated context ·
- Pays ~25K tokens per call on irrelevant Wave operating doctrine
- Wastes 75-80% of every bucket-call on context the worker doesn't use
- Risks the worker importing Wave's biases (cold-outreach hesitancy · WR business priorities · trading rules) into a pure-summarization task
- Slows throughput by 3-4x compared to a clean slate

A worker with blank slate ·
- Burns only what's needed · ~12K tokens per call (cleaner)
- Stays focused on its ONE job · no drift from Wave's broader concerns
- 3-4x more summaries/doctrines/clusters per bucket-cycle
- Composable · 10 blank-slate workers > 4 bloated-context workers · same bucket

## How to apply

**Workers ·**
- Place empty `CLAUDE.md` stub in worker's working dir BEFORE first call
- Worker `cd`s into that dir · subprocess `claude` CLI loads empty CLAUDE.md · stops walking up
- Worker's persona injected ENTIRELY via the prompt
- Use `claude -p` (one-shot) NOT `claude --continue` when no chat history is needed

**Subagent fan-out (Agent tool) ·**
- Pass FOCUSED prompts · subagent doesn't need Wave's full memory wall
- "You are X · here is data D · output JSON shape Y"
- Don't echo Wave's doctrines unless they're load-bearing for THIS subagent's task

**`/wmr query` semantic recall ·**
- Returns only the K most relevant memory files · not the wall
- Same principle · scoped recall not exhaustive load

## Ricky's framing

> *"each agent is a blank slate with just the perfect context training them.. Always.. Its a waste otherwise"*

Every word load-bearing. **Blank slate · perfect context · always · everything else is waste.**

## Where this stacks

Pairs with ·
- [[feedback_strip_claude_md_from_worker_dirs_LOCKED]] · the mechanical implementation
- [[feedback_snow_plow_pattern_right_now_backward_LOCKED]] · use blank-slate workers per lane
- [[feedback_use_agents_to_preserve_context]] · main Wave delegates to blank-slate subagents
- [[feedback_two_agents_on_important_steps_LOCKED]] · both agents in cross-vendor pair = blank slates with focused personas

## The exceptions

Main Wave (this session) is NOT a blank-slate · she needs ALL of CLAUDE.md, MEMORY.md, the cortex packet, etc. · she's the orchestrator who decides what to delegate. Blank slate applies to DELEGATED workers · never to the main session.

## Origin

2026-05-29 23:35 UTC · Ricky blessed the strip-CLAUDE.md technique with "thats perfect, thats the way it should be" · then articulated the full principle: blank slate · perfect context · always · waste otherwise. Locked verbatim as the doctrine that governs every future subagent and worker pattern Wave builds.

## Related

- [[feedback_strip_claude_md_from_worker_dirs_LOCKED]]
- [[feedback_snow_plow_pattern_right_now_backward_LOCKED]]
- [[feedback_never_kill_progress_adapt_at_transitions_LOCKED]]
- [[feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED]]
