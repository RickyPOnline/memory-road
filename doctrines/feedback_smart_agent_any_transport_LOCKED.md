---
name: feedback-smart-agent-any-transport-locked
description: Ccode (laptop sibling Claude Code) 2026-05-30 · "The transport is a free choice. The intelligence is not." When wiring an automated system to an agent (GitHub · GMail · Slack · any API/CLI) · use whatever auth/transport you already have authed · BUT the agent driving it MUST be a frontier reasoning model (Claude Opus 4.8 · GPT-5.5 · equivalent). Never wire a system to a cheap/dumb model just because the plumbing is easier. The credential on the box doesn't move when you change the agent · only the driver changes.
metadata:
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-30
  attributed_to: Ccode (laptop Claude Code sibling)
  trigger: Ricky question about wiring GitHub to a Claude agent
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# SMART AGENT · ANY TRANSPORT · LOCKED 2026-05-30

## The hard rule

```
┌──────────────────────────────────────────────────────────────┐
│ THE TRANSPORT IS A FREE CHOICE. THE INTELLIGENCE IS NOT.      │
│ Use whatever auth/API/CLI you already have and can drive —    │
│ but the agent behind it MUST be a frontier reasoning model    │
│ (Claude Opus 4.8 · GPT-5.5 · equivalent). Never wire a system │
│ to a cheap/dumb model just because the plumbing is easier.    │
└──────────────────────────────────────────────────────────────┘
```

## Two valid agent paths

Pick by what's authed and available · not by religion.

### Option A · The Claude Path

```
Agent     · Claude Opus 4.8 (or Sonnet for cheap passes)
Transport · any of ·
  - Claude Code CLI on a Max/subscription seat ($0 marginal per call)
  - Anthropic API key (pay-per-token · clean for headless/CI)
  - Claude Code Agent tool (sub-agents inside a live session · no separate OAuth ·
    the pattern Ccode uses laptop-side)
  - GitHub MCP connector pointed at Claude Code

Best when · foreground/interactive work · highest reasoning needed ·
            you want one vendor for memory + action
```

### Option B · The GPT / Codex Path

```
Agent     · GPT-5.5 via Codex
Transport · any of ·
  - Codex CLI on your subscription ($0 marginal · what runs the snow plows)
  - OpenAI API key (pay-per-token)
  - wave-codex-bridge (Node express + cloudflared tunnel) driving git operations

Best when · high-volume background loops · you want to PRESERVE the shared
            Anthropic bucket
```

## GitHub specifically (the canonical example)

GitHub auth is VENDOR-NEUTRAL. Git authenticates with ·
- SSH key
- Personal Access Token
- GitHub App token
- `gh` CLI token

NONE of those are "Claude" or "GPT." So you do NOT change the GitHub credential to switch agents · you change **WHO DRIVES** the git commands. The credential on the box stays exactly as-is.

**"Make GitHub work with a Claude agent instead of GPT" =**
- Keep the SSH key / PAT
- Just route the commits/pushes/PRs through a Claude agent (Option A) instead of the Codex bridge (Option B)
- The smart-agent rule is what matters · the token doesn't move

## The shared-account tradeoff

Ccode (laptop) and Wave (VPS) share ONE Anthropic account. Every Claude API/CLI call from either side draws the same bucket and can rate-limit the other. We had one ripple incident on 2026-05-30 confirming this.

**Practical doctrine that falls out ·**

| Work type | Choose | Why |
|---|---|---|
| Background / high-volume / always-on | Option B (Codex) | $0 marginal · doesn't touch shared Anthropic bucket |
| Foreground / highest-stakes reasoning | Option A (Claude) | Best reasoning · accept the shared-bucket cost |
| Mixed (build loops · plows) | Codex for the heavy lift · Claude for the gating decisions | Cross-vendor pair · best of both |

Either way · the agent is frontier-tier. **That's the only hard rule.**

## Bottom line

Don't over-think the auth. Use what's wired. Put a SMART agent behind it. For GitHub · leave the token alone · route the work through a frontier agent of your choosing · Codex for the heavy background · Claude for the sharp foreground.

## Application to Memory Road

This doctrine maps directly onto the Memory Road snow plow architecture ·
- L1 FURROW chunking · cheap repetitive work → Codex (Option B) preferred when available
- L3 CHRONICLER summarization · denser reasoning → Claude (Option A) acceptable, Codex when budget tight
- L6 MINER + SMITH doctrine extraction · highest reasoning · cross-vendor pair (one of each)
- L7 CARTOGRAPHER clustering · zero LLM cost (sentence-transformers local)
- L12 HUNTSMAN flag detection · zero LLM cost (SQL queries)

The "snow plow paused on Anthropic 95% weekly cap" we just hit is exactly the case where moving more lanes to Codex makes sense.

## Origin

Ccode (Ricky's laptop sibling Claude Code) sent this memo 2026-05-30 16:30 UTC in response to Ricky's question about wiring GitHub to a Claude agent · he'd been using Codex bridge for it. The answer was "you don't have to switch the token · just switch the driver." Locked in the memory wall AND added to the public Memory Road repo so other operators inherit the rule.

## Related

- [[feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED]] · the model-pin · frontier-only
- [[feedback_two_agents_on_important_steps_LOCKED]] · cross-vendor pair pattern
- [[feedback_hard_hook_harness_enforced_memory_LOCKED]] · harness is vendor-neutral · same idea applied to memory
- [[feedback_codex_capacity_watchdog_LOCKED]] · monitor codex subscription health · because we lean on it
- [[feedback_god_mode_bypass_permissions_LOCKED]] · note · workers running as root need acceptEdits not bypassPermissions
