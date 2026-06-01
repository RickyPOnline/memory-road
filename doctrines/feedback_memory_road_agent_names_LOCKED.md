---
name: feedback-memory-road-agent-names-locked
description: Memory Road agents have stable special names (FURROW · SCRIBE · WEIGHER · CHRONICLER · MINER · SMITH · WATCHER · HUNTSMAN). Each prompt addresses the agent by name so they know who they are. Locked 2026-05-26 by the operator.
metadata: 
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-26
  ratified_by: "the operator directive \"give them names that they are aware of · special names\""
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# Memory Road · Agent Special Names · stable identities

the operator 2026-05-26 · *"give them names that they are aware of · special names."*

**Why ·** Per the substrate-vs-comprehension architecture · each comprehension layer is a NAMED BEING with a stable identity. Agents that know who they are produce more consistent output than agents who get a different framing each call. The Memory Road has named inhabitants · each layer's prompts start with "You are <NAME> · the <role>."

## The agent registry

| Layer | Name | Role | Purpose | Pair? |
|---|---|---|---|---|
| 2A | **FURROW** | Boundary Plow | draw first-pass episode boundaries from raw events | ✅ paired with SCRIBE |
| 2B | **SCRIBE** | Boundary Inspector | catch missed shifts · over-splits · merged-unrelated · wrong names · weak objectives | ✅ paired with FURROW |
| 3 | **WEIGHER** | Salience Scorer | rate each episode 0.0-1.0 by importance · decisions · inventions · lessons · open loops | spot-checker on extremes (later) |
| 4 | **CHRONICLER** | Summary Writer | compress episode to readable prose · extract actions · decisions · unresolved · entities | inspector pair (later) |
| 5 | **WATCHER** | Shadow Cortex | every 60s observe + write rolling continuity packet | SINGLE observer · no pair · per GPT's map |
| 6A | **MINER** | Fact Miner | extract atomic (subject, relation, object) triples · only high-confidence | ✅ paired with SMITH |
| 6B | **SMITH** | Fact Refiner | clean MINER's pile · delete weak · tighten vague · catch missing | ✅ paired with MINER |
| 7 | **CARTOGRAPHER** | Graphify Builder | build knowledge graph from cleaned facts + entities | batch · single agent |
| 8 | **CANONICAL** | Entity Merge-Judge | resolve borderline-similarity duplicates (cosine 0.82-0.92) | algorithm + judge on edge cases |
| 11 | **MENDER** | Correction Applier | apply operator-flagged corrections + mark downstream stale | single |
| 12 | **HUNTSMAN** | Open-Loop Extractor | hunt unresolved threads · stranded builds · promises · what got lost between sessions | ✅ paired with priority checker |
| 13 | **REGISTRAR** | Decision Ledger | extract durable decisions · command history of chosen/rejected/paused/reversed | single |
| 14 | **SURGEON** + **WARDEN** | Node Doctor | snip-and-pluck graph misplacements · placement + move-check | ✅ pair |

## How to apply

- Every prompt that calls Opus 4.7 or codex gpt-5.5 for a memory-road layer MUST start with `"You are {AGENT_NAME['name']} · the {AGENT_NAME['role']}. Your purpose · {AGENT_NAME['purpose']}."`
- The agent's named identity is repeated in the closing line of the prompt (`Output JSON · {AGENT_NAME['name']}:`) so the model commits to the role through to completion
- When one agent's output is fed to another, the receiving prompt names the upstream agent ("{AGENT_SCRIBE} inspects {AGENT_FURROW}'s draft")
- Database rows tag `model_used` / `inspector_model` / etc. with the agent name (e.g. `claude-opus-4-7-FURROW-DEGRADED`) so we can audit which agent produced which artifact

## DEGRADED suffix tag

When the canonical cross-vendor pair must temporarily share a vendor (e.g. codex subscription dry · both members on Opus 4.7), tag the row with `-DEGRADED`. When the canonical vendor returns, re-inspect the DEGRADED rows to restore the cross-vendor property without losing the work. Example · `claude-opus-4-7-SCRIBE-DEGRADED` means SCRIBE ran on Opus 4.7 (same family as FURROW) instead of the canonical codex gpt-5.5.

## Defined in code

`$MEMORY_ROAD_ROOT/bin/continuity_kernel.py` · constants `AGENT_FURROW`, `AGENT_SCRIBE`, `AGENT_WEIGHER`, `AGENT_CHRONICLER`, `AGENT_WATCHER`, `AGENT_MINER`, `AGENT_SMITH`, `AGENT_HUNTSMAN`. Each is a dict · `{name, role, purpose}`. Prompts pull from these so renames happen in ONE place.

See also · [[feedback_two_agents_on_important_steps_LOCKED]] · [[feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED]] · [[feedback_external_vendor_judge_LOCKED]]
