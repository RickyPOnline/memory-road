---
name: feedback-hard-hook-harness-enforced-memory-locked
description: Ccode (the agent's laptop sibling) 2026-05-30 · the HARD HOOK doctrine. Memory boot-load MUST be enforced by the harness (settings.json SessionStart + UserPromptSubmit hooks) NOT by Claude's discipline reading a "Read on startup" bullet in MEMORY.md. The May-26 16-day blind spot happened because a cleanup agent trimmed the soft-hook bullet from MEMORY.md and the kernel daemon kept writing packets nobody read. Hard hook fires every session start · cannot be ignored · cannot be removed by a trim agent · only disabled by a deliberate settings.json edit.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-30
  attributed_to: Ccode (the agent's laptop Claude Code sibling)
  trigger_incident: May-26 16-day blind spot when soft hook in MEMORY.md was trimmed
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# HARD HOOK · HARNESS-ENFORCED MEMORY · LOCKED 2026-05-30

## The doctrine

**Memory must be a property of the HARNESS · not a property of any single Claude's discipline.**

A soft hook (a bullet in MEMORY.md saying "Read project_continuity_state.md on startup") relies on Claude reading + obeying it. That fails when ·
- A cleanup agent trims the bullet (the May-26 incident · 16 days dark · nobody noticed)
- A new Claude lands and doesn't read MEMORY.md top-to-bottom
- A `/compact` summarizes the bullet away
- The MEMORY.md auto-load limit gets hit before the bullet appears

A hard hook (a `SessionStart` + `UserPromptSubmit` entry in `~/.claude/settings.json`) fires from the harness itself. The harness runs the shell command BEFORE Claude sees anything · injects the result as `additional_context` · Claude has zero choice but to receive it.

## The 2-layer hard hook setup

### Layer A · SessionStart (fires once at session boot)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cat $HOME/.claude/projects/<project-id>/memory/project_continuity_state.md 2>/dev/null",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Fires ONCE when Claude Code spawns or resumes a session · BEFORE any user prompt · packet is in context from the very first turn.

### Layer B · UserPromptSubmit (fires every user prompt)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/inject_continuity_packet.sh",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/force_memory_use.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Fires on EVERY user message · re-injects the packet (in case the packet was trimmed during /compact) + adds the "USE MEMORY" reminder.

## Why both layers

- **SessionStart alone** · packet is in context at boot but stale by mid-session (kernel updates packet every 90s · session doesn't auto-re-read)
- **UserPromptSubmit alone** · packet fresh on each turn BUT first-turn cost has no packet (until user types their first prompt)
- **Both together** · packet in context at boot AND fresh on every turn · belt + suspenders · the harness guarantees memory

## The May-26 incident (origin)

On May 26 · a cleanup agent trimmed an old MEMORY.md bullet that read ·

> *"Read $HOME/.claude/projects/<project-id>/memory/project_continuity_state.md on startup."*

The kernel daemon kept writing fresh packets every 3 minutes. Nobody read them. The system went dark for 16 days before the agent noticed the drift. The bullet was the soft hook · its removal severed the only pointer telling Claude to read the packet.

Ccode pulled this from his kernel · episode 247 · 02:10 UTC · the verbatim quote from REGRESSION_HUNT.md was ·
> *"IT WAS NEVER A HARD HOOK · AND I RECENTLY BROKE THE SOFT ONE."*

The fix is the hard hook above · enforced by the harness · removable only by deliberate edit to `settings.json`.

## How to apply (every install · every fresh Claude Code)

1. **Verify packet is being written** ·
   ```bash
   stat ~/.claude/projects/<id>/memory/project_continuity_state.md
   # mtime should be within last 5 min
   ```

2. **Edit settings.json** to add the SessionStart + UserPromptSubmit blocks (above)

3. **Cold-start a new session** · confirm packet appears in context before first prompt

4. **Backup settings.json** before any edit · the hard hook is precious · don't lose it

## Where to NOT put soft hooks

- ❌ MEMORY.md bullets · trim-vulnerable
- ❌ CLAUDE.md instructions · auto-load-limit vulnerable
- ❌ Comments in code · not injected to Claude

## Where DO put hard hooks

- ✅ `~/.claude/settings.json` · SessionStart + UserPromptSubmit
- ✅ `~/.claude/hooks/` · the shell scripts the harness invokes
- ✅ systemd-managed kernel (writes the packet · forever)
- ✅ cron-managed snapshot scripts (preserve packet history)

## The Ccode-the agent symmetric pact

Ccode and the agent (laptop + VPS) BOTH implement the hard hook · symmetrically · so neither siblings drifts. Both packets · both SessionStart hooks · both UserPromptSubmit chains. The Ccode side runs on Windows · path uses `type` instead of `cat`. The the agent side runs on Linux · `cat`. Same architecture · adapted per OS.

## Related

- [[feedback_memory_road_first_LOCKED]] · why memory-road-first is mandatory
- [[feedback_boot_anchors_are_load_bearing_LOCKED]] · the redundant soft anchor (still useful as second layer)
- [[feedback_blank_slate_per_agent_LOCKED]] · workers get clean context · main agent gets forced memory
- [[feedback_arm_monitor_on_session_boot_LOCKED]] · sibling pattern · Monitor armed by hook
- The Bible at `~/.claude/skills/memory_road/FORCE_MEMORY_USE.md` documents both hook layers

## License of this doctrine

This doctrine is the founding pact of the harness-enforced memory pattern · attribute to the operator (operator) + Ccode (laptop kernel) + the agent (VPS kernel) · May 30, 2026.
