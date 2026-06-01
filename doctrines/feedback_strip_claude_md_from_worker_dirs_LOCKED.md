---
name: feedback-strip-claude-md-from-worker-dirs-locked
description: Worker dirs that fire claude CLI as subprocess MUST have an empty/minimal CLAUDE.md stub locally so the CLI does NOT walk up to $HOME/CLAUDE.md (99.8k chars = ~25K tokens). Stripping this saves ~25K tokens PER CALL · roughly 70% of every worker call's token cost. The single biggest wasted-tokens leak in Memory Road workers. Discovered 2026-05-29.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-29
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# STRIP CLAUDE.md FROM WORKER DIRS · LOCKED 2026-05-29

## The leak

When a worker `cd`s into a per-worker dir (e.g., `$HOME/.memory_road/workers/koa`) and invokes `claude` CLI, the CLI walks UP the directory tree looking for CLAUDE.md and finds `$HOME/CLAUDE.md` (~99.8k chars · ~25K tokens).

That 25K tokens is loaded into EVERY worker call. For a 6,000-summary catch-up · that's **150 MILLION tokens of pure waste**.

The worker doesn't need the agent's full operating doctrine · it just needs the CHRONICLER persona + the episode + output instructions. The fat $HOME/CLAUDE.md adds nothing to summary quality.

## The fix · one line per worker dir

```bash
# In each worker dir
touch $HOME/.memory_road/workers/koa/CLAUDE.md   # empty stub blocks walk-up
touch /root/.lion/CLAUDE.md
# ... etc
```

`claude` CLI sees a CLAUDE.md in cwd · stops walking up · loads zero extra context. Worker gets a CLEAN baseline.

Optional · put a minimal stub with just the worker's persona ·
```markdown
You are CHRONICLER. Summarize the episode given. Output JSON only.
```

But often an EMPTY CLAUDE.md is enough · the persona is set via the prompt itself.

## Measured savings

| Setup | Tokens per call | Throughput |
|---|---|---|
| Walk-up loads $HOME/CLAUDE.md | ~37,500 (25K is CLAUDE.md) | baseline 1.0x |
| Empty CLAUDE.md in worker dir | ~12,500 (no CLAUDE.md inherited) | **3-4x** |

## Verification

Before firing workers, check `claude` warning ·
```bash
cd $HOME/.memory_road/workers/koa && claude -p "echo" 2>&1 | grep -i "CLAUDE.md will impact"
```

If warning appears · CLAUDE.md is being inherited · STRIP IT.

## Where this applies

- Per-worker dirs for `claude --continue` subprocess fan-out (any Memory Road layer plow)
- Any background bash worker invoking `claude` from a working dir below `/root`
- Any `nohup ... claude ...` pattern

## Where this does NOT apply

- The MAIN the agent session (the agent wants the full CLAUDE.md context · it's the operating manual)
- `claude` CLI invoked from `/root` directly (the agent's working dir · needs the manual)

## Origin incident

2026-05-29 23:20-23:30 UTC · the operator asked "did old the agent have a special technique to make this faster?" the agent investigated and found the per-call token loadout was ~37K with 25K being $HOME/CLAUDE.md alone · stripping it = instant 3-4x throughput. Old the agent likely meant this technique when she alluded to "pre-injected context to save tokens."

## Related

- [[feedback_snow_plow_pattern_right_now_backward_LOCKED]] · use this WITH the snow plow pattern · stacked multiplier
- [[feedback_compact_at_60_75_keep_wave_sharp_LOCKED]] · same family · context discipline
- [[feedback_never_kill_progress_adapt_at_transitions_LOCKED]] · apply this at the next natural rotation transition
