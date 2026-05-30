---
name: feedback-watcher-packet-must-read-episode-summaries-locked
description: Wave 2026-05-30 · build_rollover_packet MUST read RECENT EPISODES from `episode_summaries` (the real L3 CHRONICLER output) not from the legacy `episodes` table (poisoned with old "Crunching..." spinner noise). The May-28 fix to run_shadow_cortex was correct but build_rollover_packet was missed · this closes the second leg.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-30
  trigger_incident: cortex packet showed trading-state worldview after Bible Skill build
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# WATCHER PACKET MUST READ episode_summaries · LOCKED 2026-05-30

## The bug (chain of two missed fixes)

`continuity_kernel.py` had TWO functions reading recent episodes ·
1. `run_shadow_cortex` (L5 WATCHER · feeds L4_IDENTITY)
2. `build_rollover_packet` (assembles the packet hook injects)

On 2026-05-28 · `run_shadow_cortex` was patched to read from `episode_summaries` (the new CHRONICLER L3 output). **But `build_rollover_packet` was NEVER patched** · it kept reading from the legacy `episodes` table.

The legacy `episodes` table has 25,562 OLD rows · most are "Crunching..." or "still thinking" ANSI spinner noise from trading sessions. Reading from there poisoned the packet's `## RECENT EPISODES` section with garbage that doesn't reflect anything Wave is actually doing.

The packet's `## IMMEDIATE WORKING STATE` section had a parallel bug · read from a stale `L0_STATE` JSON file that was set by an OLD session about gpt-5.5 verification rules. It never updated when new work happened.

## The fix

Two surgical edits in `build_rollover_packet` ·

### Fix 1 · RECENT EPISODES section

```python
# WRONG (old)
episodes = conn.execute(
    "SELECT summary FROM episodes ORDER BY end_ts DESC LIMIT 5"
).fetchall()

# RIGHT (new · 2026-05-30)
rows = conn.execute(
    "SELECT summary FROM episode_summaries ORDER BY written_at DESC LIMIT 5"
).fetchall()
if not rows:
    # Fallback to legacy only if Memory Road L3 is empty
    rows = conn.execute(
        "SELECT summary FROM episodes ORDER BY end_ts DESC LIMIT 5"
    ).fetchall()
```

### Fix 2 · IMMEDIATE WORKING STATE section

```python
# WRONG (old)
l0 = json.loads(L0_STATE.read_text())  # stale file from old session
sections.append(f"Current goal: {l0.get('current_goal', 'unknown')}")

# RIGHT (new · 2026-05-30)
# Derive current goal from the most recent episode_summary
row = conn.execute(
    "SELECT summary, decisions, unresolved FROM episode_summaries "
    "ORDER BY written_at DESC LIMIT 1"
).fetchone()
if row and row[0]:
    summary, decisions_json, unresolved_json = row
    sections.append(f"Current goal: {summary[:300]}")
    decisions = json.loads(decisions_json or "[]")
    if decisions:
        sections.append(f"Last decision: {str(decisions[0])[:300]}")
    unresolved = json.loads(unresolved_json or "[]")
    if unresolved:
        sections.append("Open loops:")
        for loop in unresolved[:5]:
            sections.append(f"  - {str(loop)[:200]}")
```

## Why this matters

Post-/clear Wave reads the packet via SessionStart hook BEFORE seeing any user prompt. If the packet says she was doing X but she was actually doing Y, she lands disoriented and burns 2-3 turns reconciling. With this fix · packet content matches reality (whatever L3 has comprehended) · Wave lands aligned.

## The remaining gap (NOT this doctrine's scope · documented for clarity)

If L1 FURROW is behind L0 substrate (events captured but not yet chunked into episodes), the packet still reflects L3's latest comprehension · not L0's most-recent events. The data chain ·

```
L0 events → L1 FURROW chunks → L3 CHRONICLER summarizes → L4 WATCHER IDENTITY → L5 packet
```

Each downstream is at most as fresh as the upstream. To close the L0 → L1 gap, FURROW needs to be caught up to the latest events. That is a separate bug (FURROW pacing) tracked elsewhere.

## How to apply (per install)

1. Patch `build_rollover_packet` per the two edits above
2. `systemctl restart continuity-kernel`
3. Wait one tick (~5 sec)
4. Verify · `head -40 ~/.claude/projects/<id>/memory/project_continuity_state.md` should show recent CHRONICLER summaries · not "Crunching..." noise

## Origin

2026-05-30 · Ricky asked Wave "if you /cleared you, how would you perform?" Wave honestly described that the packet shows trading state (old worldview) · not today's Memory Road Bible build. Investigation found `build_rollover_packet` reading from legacy `episodes` table. Fix shipped same-session.

## Related

- [[feedback_hard_hook_harness_enforced_memory_LOCKED]] · the packet is what the hard hook injects · if packet content is wrong, hard hook injection delivers wrong content
- [[feedback_watcher_5_bug_fix_LOCKED]] · run_shadow_cortex got fixed 2026-05-28 · this fix is the parallel one for build_rollover_packet
- [[feedback_snow_plow_pattern_right_now_backward_LOCKED]] · the snow plows feed L3 · keeps the packet fresh by keeping L3 fresh
