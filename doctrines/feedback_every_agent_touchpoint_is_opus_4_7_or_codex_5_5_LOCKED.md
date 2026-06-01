---
name: feedback-every-agent-touchpoint-is-opus-4-7-or-codex-5-5-locked
description: Every spot a the agent agent touches uses Claude Opus 4.7 OR codex gpt-5.5 · no mid-tier · no exceptions. Locked 2026-05-26 by the operator.
metadata: 
  node_type: memory
  type: feedback
  status: LOCKED
  established: 2026-05-26
  originSessionId: e3c6788c-6e96-4357-a8f9-25b72abf0e69
---

# Every agent touchpoint · Opus 4.7 or codex gpt-5.5 · no exceptions

the operator 2026-05-26 · *"Every damn spot an agent touches · GPT 5.5 or Claude 4.7 or both · it's that simple."*

**Why ·** Sonnet-mid-tier · Haiku-cheap-tier · gpt-4o · gpt-4o-mini · all silently swallow quality at every layer. The best house in town doesn't use lumber from the discount aisle. the agent's memory · the doctrines · the customer rebuilds · every place an agent makes a decision · gets a top-shelf model.

**How to apply ·**
- Code · any constant or routing that pins a model defaults to `claude-opus-4-7` (Anthropic) OR `gpt-5.5` (codex CLI · subscription) · never anything else
- Specs · when proposing a new agent-touched layer, say which of the two models powers it · and why
- Old code that still references `gpt-4o-mini` · `gpt-4o` · `sonnet-4-6` · `claude-haiku-4-5` · etc. is LEGACY · either swap to Opus 4.7 or codex 5.5 OR explicitly tag `LEGACY-DO-NOT-RESURRECT`
- The PAIRING happens per-layer · two agents only where meaning can be wrong (see [[feedback_two_agents_on_important_steps_LOCKED]]) · the model pin applies to BOTH members of any pair
- The cross-vendor split (when a pair needs different vendors per April-14 doctrine) · 1 Claude Opus 4.7 + 1 codex gpt-5.5 · permanent

**Counter-rule ·** when GPT/Ccode/skeptic_loop suggests a fallback to DeepSeek / Sonnet / Haiku · refuse · per the no-deepseek doctrine and this one. Only acceptable fallback for codex is · retry codex with backoff · OR escalate to the operator with the trace.

See also · [[feedback_use_codex_cli_never_bug_ricky_about_openai_top_up_LOCKED]] · [[feedback_external_vendor_judge_LOCKED]] · [[feedback_no_deepseek]] · [[feedback_two_agents_on_important_steps_LOCKED]]
