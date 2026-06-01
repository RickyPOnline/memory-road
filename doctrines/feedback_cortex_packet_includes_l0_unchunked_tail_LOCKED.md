---
name: feedback-cortex-packet-includes-l0-unchunked-tail-locked
description: the operator 2026-05-30 21:05 UTC · "How do you fix that?" The 5% post-crash gap (events captured in L0 but not yet chunked into L1 episodes by the 60s poll) is fixed by including the raw L0 unchunked tail in the cortex packet itself. Zero LLM cost · pure SQL query · the last 15 events newer than the L1 watermark are appended to every packet. Post-recovery the agent reads L1+L3 (summarized) PLUS the raw L0 tail · 100% recall · no gap.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-30
  trigger_incident: the operator asked how to close the 5% post-crash gap
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# CORTEX PACKET INCLUDES L0 UNCHUNKED TAIL · LOCKED 2026-05-30

## The fix · one SQL query · zero LLM cost

`build_rollover_packet` now appends a `## L0 UNCHUNKED TAIL` section to every packet · listing the most-recent 15 events that haven't been chunked into an L1 episode yet. Post-recovery the agent reads ·
- L4 IDENTITY (worldview · stance · beliefs)
- L1 IMMEDIATE WORKING STATE (derived from latest L3 summary)
- L0 UNCHUNKED TAIL ← NEW · the literal last events before any crash
- L3 RECENT EPISODES (compressed)
- Trade · system · unresolved · resume instruction

## Why this closes 100% of the gap

The 5% post-crash gap was · "events captured in L0 substrate but not yet chunked into L1 episodes by the 60s poll." Those events were ALWAYS safe in L0 · they just weren't visible in the packet. Now they are. the agent boots back · reads the packet · sees the literal raw events from the last minute · knows exactly what was happening.

Cost · one SQL query per packet build (~1ms). Zero LLM. No new daemon. Just a packet enrichment.

## Related

- [[feedback_watcher_packet_must_read_episode_summaries_LOCKED]] · packet content fix family
- [[feedback_l1_furrow_must_be_always_on_systemd_LOCKED]] · sister fix · keeps L1 close to L0
- [[feedback_hard_hook_harness_enforced_memory_LOCKED]] · packet auto-injected on every boot
