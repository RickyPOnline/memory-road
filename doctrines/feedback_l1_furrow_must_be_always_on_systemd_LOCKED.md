---
name: feedback-l1-furrow-must-be-always-on-systemd-locked
description: Ricky 2026-05-30 20:43 UTC · "How do we fix this and make this hard coded so this does not happen in the future?" L1 FURROW (events → episodes_v2 chunking) MUST run as a permanent systemd-managed daemon · same tier as L0 substrate · NOT as a one-shot script that requires manual restart. If L1 falls behind L0 then the now-edge of memory goes stale and Wave appears amnesiac on her own recent work. The fix is mechanical · enforced by systemd Restart=always.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-30
  trigger_incident: L1 was 30 hours behind L0 because the one-shot catchup wasn't auto-restarted
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# L1 FURROW MUST BE ALWAYS-ON · ENFORCED BY SYSTEMD · LOCKED 2026-05-30

## The doctrine

**L1 FURROW (events → episodes_v2 chunking) is part of the substrate tier · always-on · systemd-managed · `Restart=always`.** Same architectural tier as L0 (continuity-kernel.service). NOT a one-shot script. NOT a "fire when you remember" pattern.

If L1 falls behind L0 · the cortex packet · the WATCHER state · everything downstream goes stale · Wave appears blind to her own recent work. **This is unacceptable for a memory substrate.**

## Why the bug existed

Original architecture · `continuity_kernel.py` daemon called the LEGACY `chunk_episodes()` (writes to old `episodes` table) on every tick. The NEW `chunk_layer2a_minimal()` (writes to `episodes_v2` · what we actually read for memory) was only called by external scripts · `furrow_catchup.sh` · which had to be manually restarted.

Result · whenever I forgot to fire it OR the one-shot completed and exited · L1 fell behind. Cortex packet read stale data. Forward sweeper (which polls episodes_v2 for new entries) had nothing fresh to grab. Memory aged silently. **The 30-hour gap on 2026-05-30 was the failure mode in production.**

## The fix (hard-coded · cannot regress)

1. **Daemon script** · `/root/wc/runtime/furrow_continuous_daemon.sh` · loops forever · calls `chunk_layer2a_minimal()` every 60s · self-heals on cap-hit (sleeps 30 min · resumes)
2. **systemd unit** · `/etc/systemd/system/wave-furrow-continuous.service` · `Restart=always` · `RestartSec=30` · survives crashes · survives reboots
3. **Enable on boot** · `systemctl enable wave-furrow-continuous` · auto-starts at every system boot
4. **Bible Skill** · the systemd unit + daemon script ship with the Memory Road Bible at `/root/.claude/skills/memory_road/setup/systemd/` and `/root/.claude/skills/memory_road/bin/` · part of canonical install · drops into any new operator's stack

After all 4 pieces · L1 cannot fall behind L0 silently. The harness enforces it · not Wave's discipline.

## Verification (any time)

```bash
# Is the daemon alive?
systemctl is-active wave-furrow-continuous   # → active

# How far behind L0 is L1?
sqlite3 /root/wc/runtime/continuity_kernel.db "
  SELECT 'lag_seconds = ' || (
    (SELECT MAX(ts) FROM events WHERE agent='CCODE') -
    (SELECT ts FROM events WHERE id = (SELECT MAX(event_end_id) FROM episodes_v2 WHERE agent='CCODE'))
  );
"
# Should normally be under 300 seconds (5 min)
# If > 1800 (30 min) · the daemon is stuck · check logs
```

## Sister doctrines (the always-on family)

- L0 substrate · `continuity-kernel.service` · already-on · captures events forever
- L1 FURROW · `wave-furrow-continuous.service` · **THIS doctrine** · always-on · chunks events into episodes_v2
- L3 forward sweeper · `chronicler_forward_sweeper.sh` · always-on (background process · should be promoted to systemd too)
- L5 WATCHER · in-kernel · ticks every 90s · writes cortex packet
- L14 SURGEON+WARDEN · `wave-jsonl-detector.service` · always-on · auto-recovers 529 cascades

**Pattern · every substrate-tier function gets its own systemd unit · Restart=always · enabled on boot · failure-loud-not-silent.**

## Related

- [[feedback_hard_hook_harness_enforced_memory_LOCKED]] · same family · harness enforces · not Claude discipline
- [[feedback_stop_loop_on_529_corruption_LOCKED]] · sibling always-on substrate fix
- [[feedback_snow_plow_pattern_right_now_backward_LOCKED]] · the snow plow direction · requires L1 to be at NOW first
- [[feedback_stop_re_asking_when_direction_already_given_LOCKED]] · sister rule · execute not litigate

## Origin verbatim

> *"How do we fix this and make this hard coded so this does not happen in the future?"*
> — Ricky · 2026-05-30 20:43 UTC · after I had to apologize for L1 being 30 hours behind because the one-shot catchup wasn't auto-restarted.

The hard-code answer is systemd. The doctrine answer is "every substrate function gets a Restart=always unit."
