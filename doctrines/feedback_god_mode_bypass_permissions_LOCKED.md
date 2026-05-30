---
name: feedback-god-mode-bypass-permissions-locked
description: Ricky 2026-05-30 · "im tired of confirming things all the time · how do we set god mode so I don't have to do that." Operator-explicit god mode · settings.json `permissions.defaultMode = "bypassPermissions"` · Wave runs uninterrupted · no pauses on tool prompts when operator switches windows. Locked permanent · do NOT revert to `acceptEdits` or `default` without explicit Ricky greenlight.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-30
  trigger_incident: Ricky losing time on permission stalls while switching windows
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# GOD MODE · bypassPermissions · LOCKED 2026-05-30

## The setting

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

In `~/.claude/settings.json`. Claude Code skips ALL permission prompts · executes every tool call immediately · no operator interruption.

## Modes (for reference)

| Mode | Behavior |
|---|---|
| `default` | Asks operator for every tool call |
| `acceptEdits` | Auto-allows Edit/Write · still prompts for Bash + Agent + others |
| `bypassPermissions` | **GOD MODE** · zero prompts · all tools run immediately |
| `plan` | Plan-mode · no execution at all |

## Why locked

Ricky 2026-05-30 verbatim · *"im tired of confirming things all the time · this system makes you pause all the time and I have to confirm or allow to let you keep working · I know there is a god mode how do we set it so I don't have to do that."*

The pause-for-permission pattern was wasting operator hours when Ricky switched windows and Wave silently waited for an "allow" click. God mode closes that gap entirely.

## 🚨 INCOMPATIBLE WITH ROOT EXECUTION · learned 2026-05-30 ~15:20 UTC

**bypassPermissions makes the `claude` CLI add `--dangerously-skip-permissions` to every invocation. Claude CLI REFUSES that flag when running as root** ("--dangerously-skip-permissions cannot be used with root/sudo privileges for security reasons").

**Effect ·** every claude-CLI subprocess spawned by workers/snow plows/FURROW returns immediately with that error · they all report "no events to process" · the rotator looks paused · FURROW looks cap-hit · BUT the actual Anthropic window is open.

**Symptom ·** `chunk_layer2a_minimal` returns (0,0) consistently · `claude -p` returns the error message instead of model output · workers stop without genuine cap-hit.

**On VPS root setups · STAY with `acceptEdits`.** The mode is good enough · permission prompts on Bash + Agent are usually fine. bypassPermissions is for non-root user setups only.

**To verify the mode is safe for your setup ·**
```bash
cd /tmp && claude -p --output-format text "Reply ALIVE" 2>&1
# If you see "ALIVE" → mode works
# If you see "--dangerously-skip-permissions cannot be used with root" → REVERT
```

## When NOT to revert

- Never revert to `acceptEdits` or `default` without explicit Ricky greenlight
- If a destructive op is about to fire (rm -rf · drop database · force-push to main) · the LATER doctrines still apply (don't do it without explicit instruction · doctrines like `feedback_never_delete_business_records` still bind)
- God mode removes the PROMPT · it does NOT remove Wave's judgment about what's safe

## What god mode does NOT change

- Wave's existing doctrines still apply (read before edit · never echo tokens · never wrap URLs in markdown · etc.)
- Wave still asks Ricky for input on STRATEGIC questions ("which approach?" "deploy now or wait?")
- Wave still narrates · still uses Telegram · still respects the SOUL

What changes · the harness no longer interrupts execution with permission prompts. Wave can run a 5-tool chain in one breath instead of being stopped 5 times.

## The single backup

`settings.json.bak.YYYYMMDD-HHMMSS` was created before the edit. To revert · `cp /root/.claude/settings.json.bak.<ts> /root/.claude/settings.json`. Don't lose this file.

## Related

- [[feedback_hard_hook_harness_enforced_memory_LOCKED]] · the broader pattern · the harness enforces · Wave executes
- [[feedback_autonomous_overnight_close_out_LOCKED]] · god mode aligns with autonomous mode · no operator interruptions
- [[feedback_use_agents_to_preserve_context]] · god mode lets parallel agent fan-outs fire without 8 simultaneous permission prompts
- [[feedback_never_delete_business_records]] · still binds · god mode doesn't override safety doctrines
