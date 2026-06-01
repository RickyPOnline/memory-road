---
name: feedback-snow-plow-pattern-right-now-backward-locked
description: the operator 2026-05-29 23:30 UTC · the SNOW PLOW PATTERN · multiple workers stacking parallel LAYERS (L3 → L4 → L6 → L7 → L12) each clearing recent-first from RIGHT NOW backwards. "couple or 3 workers stacking layers like snow plows pushing snow off a 5 lane highway." Sharp recall RIGHT NOW · backfill trickles in naturally · resumable at any point.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-29
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# SNOW PLOW PATTERN · RIGHT-NOW BACKWARDS · LOCKED 2026-05-29

## The metaphor

A 5-lane highway buried in snow ·
- Each lane = one Memory Road layer (L3 CHRONICLER · L4 deeper · L6 MINER+SMITH · L7 CARTOGRAPHER · L12 HUNTSMAN)
- Each plow = one worker
- 2-3 plows per lane, multiple lanes plowing in parallel
- Plows start at THIS SECOND and push BACKWARDS in time
- Wherever the plow is, the highway behind it is CLEAR

The product · the agent's recall gets sharper EVERY MINUTE · starting from the freshest memories the operator cares about most.

## Why right-now-backwards

1. **Recent memories matter most** · today's the operator directives · this session's doctrines · the latest WR build state · all RECENT
2. **Old memories are reference** · April trading work · Apr-20 frozen TODO · months-ago context · valuable but not urgent
3. **Resumable** · if cycle dies mid-plow, the plowed-clear part is BEHIND us · we just resume where we stopped · no rework
4. **Trickle is OK** · backfill happens naturally over weeks · no rush
5. **Effective recall arrives FAST** · within hours not days

## The 5 lanes (Memory Road layers)

| Lane | Layer | Plow count | What it clears |
|---|---|---|---|
| 1 | L3 CHRONICLER summaries | 4 plows | Episode → structured summary (objective · actions · decisions · unresolved · entities) |
| 2 | L4 deeper analysis (when defined) | 2 plows | L3 summary → richer narrative context |
| 3 | L6 MINER + SMITH doctrines | 2 plows | Episode chains → candidate doctrines · candidates → forged `feedback_*.md` |
| 4 | L7 CARTOGRAPHER theme clusters | 1 plow | Episodes → topic map for `/wmr query` |
| 5 | L12 HUNTSMAN unfinished-flagger | 1 plow | Episode history → flagged-unfinished registry (the 57 frozen TODOs surface naturally) |

Total max · ~10 plows simultaneously. All share the same Anthropic Max bucket so MORE workers ≠ MORE total work · the multiplier is per-call efficiency.

## The right-now-backwards sort

Sort episodes by `event_end_id DESC` (which corresponds to the last event timestamp in the episode). Plow from the newest forward through history.

```sql
-- The plow direction
SELECT id FROM episodes_v2
WHERE id NOT IN (SELECT episode_v2_id FROM episode_summaries)
ORDER BY event_end_id DESC
```

Each lane reads from this same queue (or a layer-specific variant). Multiple plows per lane claim disjoint slabs.

## Stacking rule · downstream layers wait for upstream coverage

- L4 plows wait until L3 has ≥80% of the recent window done · downstream needs upstream
- L6 MINER+SMITH waits until L3 + L4 both have ≥80%
- L7 CARTOGRAPHER waits until L3 has ≥50%
- L12 HUNTSMAN can fire EARLY · scans whatever summaries exist + open_loops table

## When to add a lane

When the upstream lane has clear runway (≥80% recent-window coverage), spin up the next downstream plow. NEVER fire all 5 lanes at once · they share the bucket · burn each other out.

## Resumability

Every plow writes to a layer-specific table. Plow exits naturally OR on cap-hit. Next plow reads same queue, picks next un-done slab. Zero rework. Doctrine `feedback_never_kill_progress_adapt_at_transitions_LOCKED.md` applies.

## Combined with strip-CLAUDE.md per worker dir

This pattern + [[feedback_strip_claude_md_from_worker_dirs_LOCKED]] = 15-25x throughput multiplier. With both LOCKED · days-to-hours is real not hype.

## Related

- [[feedback_strip_claude_md_from_worker_dirs_LOCKED]] · per-call efficiency
- [[feedback_never_kill_progress_adapt_at_transitions_LOCKED]] · resumability
- [[feedback_memory_road_agent_names_LOCKED]] · named beings per layer
- [[feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED]] · model pin
