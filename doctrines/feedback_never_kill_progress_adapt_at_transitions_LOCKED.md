---
name: feedback-never-kill-progress-adapt-at-transitions-locked
description: the operator 2026-05-29 23:00 UTC · "never kill progress, never waste · always adapt when timing is congruent with transition." Never kill in-flight work to switch strategies · let the current cycle complete naturally · build the new strategy in parallel so it's ready to take the baton at the natural transition point. Applies to worker fleets · API window cycles · build-loop rounds · any long-running burn.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-29
  trigger_incident: chronicler_wave_2_in_flight_when_strategy_change_requested
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# NEVER KILL PROGRESS · ADAPT AT TRANSITIONS · LOCKED 2026-05-29

## The rule

When the operator requests a strategy change mid-burn ·

1. **DO NOT** kill in-flight workers/jobs to "start clean"
2. **DO** build the new strategy in parallel · ready to fire
3. **DO** wait for the natural transition point (current cycle's natural end · rate-window flip · job completion)
4. **THEN** hand off seamlessly · zero summaries lost · zero tokens wasted

## Why

Killing in-flight work to swap strategies ·
- Throws away tokens already burned
- Throws away rows already written
- Restarts the warm-up cost (first call always pays context overhead)
- Communicates panic · undermines the operator's trust in the agent's judgment

Waiting for natural transitions ·
- Banks the free summaries from the current burn
- New strategy gets a clean window with bucket recharged
- Build-time of new system overlaps with run-time of old · no idle wall-clock
- Shows operator that the agent thinks in cycles · not in lurches

## How to apply

**Trigger moments where this rule kicks in ·**
- In-flight worker fleet running when strategy change requested
- Current build-loop iteration mid-stream when better approach surfaces
- API rate window mid-cycle when wave-shape needs redesign
- A long-running render/scrape/migration where switching mid-job loses warmup

**The 4-step sequence ·**
1. **Acknowledge** the new strategy is better/correct
2. **Quantify** what the current cycle will still produce naturally (e.g., "~900 more summaries before the bucket dies")
3. **Build** the new system NOW · in parallel · ready to fire
4. **Hand off** at the natural transition (worker death · cap hit · window flip · render complete)

**Don't ask "should I kill it?" · default is NO.** Ask "when's the natural transition?" instead.

## The single exception

If the in-flight work is actively HARMING something (writing bad data · holding a lock · breaking a downstream system) · kill it immediately. But cap-hits, rate-limits, and graceful-fail patterns are NOT harm · they're natural cycle ends. Let them complete.

## Origin incident

2026-05-29 22:50 UTC · Chronicler the agent 2 (8 parallel workers) auto-fired by window-watchdog while the agent was discussing a strategy change with the operator (4-staggered-rotate instead of 8-batch). the agent's first instinct was to ask "kill the agent 2 now and switch immediately?" the operator overruled · "never kill progress, never waste · adapt when timing is congruent with transition." 

the agent 2 was already producing summaries. Killing it would have cost ~900 free summaries to start clean. Letting it burn naturally (~30 min until cap) bought time to build the rotator. The transition point was the natural cap-hit. Zero waste · zero idle wall-clock.

## Related

- [[feedback_autonomous_overnight_close_out_LOCKED]] · same family · keep cycling don't stop
- [[feedback_mission_completion_doctrine_LOCKED]] · 6 stop-conditions · cap-hit is NOT one of them
- [[feedback_stop_loop_on_529_corruption_LOCKED]] · explicit exception · STOP on 529 because it corrupts state
- [[feedback_over_and_beyond_test_yourself_LOCKED]] · proof-by-completion · let cycles finish to prove they work
