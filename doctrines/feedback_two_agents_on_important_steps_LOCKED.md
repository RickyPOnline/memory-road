---
name: feedback-two-agents-on-important-steps-locked
description: "Two agents (cross-vendor pair) on every important step · solo-writes only for verification/observation. The PRIME RULE from GPT's Agent Deployment Map. Locked 2026-05-26."
metadata: 
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-26
  ratified_by: GPT (Agent Deployment Map) + Ricky directive
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# Two agents on important steps · solo writes never · the PRIME RULE

Ricky 2026-05-26 · *"you neeeed 2 agents on important steps !!!!!"*

GPT (Agent Deployment Map) · *"No agents where parsing is enough. No swarm where one worker is enough. Two agents only where meaning can be wrong."*

**Why ·** Single-vendor self-review is bias-blind · the executor and reviewer share training corpus and blind spots. Single-agent solo-writes on load-bearing work fail without a check · the failure is silent until production. The cross-vendor pair (executor in one family · inspector in a DIFFERENT family) cancels the bias because the two members can't share the same blind spot. This is also how Wave doesn't drift into self-confirming hallucinations.

**How to apply (Memory Road specifically · the layered case) ·**

| Where pair is REQUIRED | Why | Pair shape |
|---|---|---|
| Layer 2 (episode chunking) | boundary errors poison everything downstream | 2A Boundary Plow (Opus 4.7 OR codex 5.5) + 2B Boundary Inspector (the OTHER vendor) |
| Layer 4 (summary) | summaries are the readable memory · loss of decisions kills value | 4A Summarizer + 4B Inspector · cross-vendor |
| Layer 6 (semantic facts) | facts become graph edges · hallucinated triples poison the graph | 6A Fact Miner + 6B Fact Refiner · cross-vendor |
| Layer 12 (open loop extractor · future) | drives execution priority · wrong priorities = wrong actions | 12A Miner + 12B Priority Checker |
| Layer 14 (node doctor · future) | graph-repair moves can break clusters | 14A Placement Scanner + 14B Move Checker |
| Any LOAD-BEARING doctrine lock | the wording binds future Wave behavior | Wave-writes + skeptic_loop judge (codex) before lock |
| Any LOAD-BEARING code edit | mutates production behavior | Wave-writes + skeptic_loop judge OR direct cross-vendor smoke-eval before apply |

**Where pair is NOT required (solo OK) ·**

| Where | Why |
|---|---|
| Layer 0 + 1 (substrate · parsing only) | no LLM · no meaning to disagree about |
| Layer 5 (Shadow Cortex · rolling snapshot) | not the archive · just a 60s observer view · single observer is correct per GPT's map |
| Layer 8 + 9 (canonicalization + union) | algorithm-first · LLM only on edge cases (the borderline-merge queue) |
| Layer 10 (vector recall at query time) | search math · no LLM |
| Verification commands · grep · stat · sqlite queries | reading the current state, not changing it |
| Smoke tests on already-applied code | observation, not construction |

**Counter-rule ·** when in doubt whether something is "important enough" · default to pair. The cost of an extra cross-vendor review is small. The cost of a silently-bad load-bearing write is huge.

**Operational ·** the pair pattern is implemented in `/root/.claude/skills/skeptic_loop/` (executor = Wave Opus 4.7 · judge = codex gpt-5.5 · target-score 5/5 · max 5 iterations). When skeptic_loop converges-broken (no score improvement across iterations), the spec is too complex for one pass · break it smaller · ship the minimal first brick · skeptic_loop the next.

See also · [[feedback_external_vendor_judge_LOCKED]] · [[feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED]] · [[feedback_actually_use_the_recursive_stack_LOCKED]] · [[feedback_no_deepseek]] · [[feedback_no_time_estimates_locked]] · [[feedback_snapshot_the_file_youre_about_to_edit_LOCKED]]
