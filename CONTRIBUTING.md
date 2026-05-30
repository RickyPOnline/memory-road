# Contributing to Memory Road

Memory Road grew out of real production failures · each one captured as a locked doctrine in `doctrines/`. The pattern that built it is the pattern that grows it.

## How to contribute

### Option 1 · Use it, report what breaks

Install Memory Road on your own Claude Code setup. Let it run for a week. Report ·
- What broke (file an issue)
- What didn't work as documented (file an issue)
- What you wish it did (file an issue · we'll tag `enhancement`)
- A wild fix idea (file an issue · we'll discuss before PR)

### Option 2 · Lock a doctrine

If you hit a real production failure and figure out the fix · capture it as a doctrine ·

```bash
# Filename pattern · feedback_<topic>_<status>.md
# Status · _LOCKED suffix means it survived adversarial review · _PROVISIONAL means pending
```

Doctrine file shape (frontmatter + the 5 required sections) ·

```markdown
---
name: feedback-your-topic-locked
description: One-sentence summary of what this doctrine prevents
metadata:
  type: feedback
  status: LOCKED
  established: YYYY-MM-DD
  trigger_incident: brief description
---

# YOUR DOCTRINE TITLE · LOCKED YYYY-MM-DD

## The rule
What is the rule, stated as an imperative.

## Why
The reason · ideally tied to a real incident.

## How to apply
Concrete trigger conditions. When does this kick in.

## The single exception
If there is one. Many doctrines have NO exception.

## Related
Links to related doctrines (use [[doctrine-slug]] syntax).
```

Submit via PR. We'll review for ·
- Concreteness (is this actually a rule or a vibe?)
- Evidence (is there a real incident behind this?)
- Specificity (does it actually prevent a failure mode?)
- Composability (does it stack with existing doctrines?)

### Option 3 · New comprehension layer

Memory Road has 11 layers. There's room for more · e.g., ·
- L8 CANONICAL (dedup near-duplicate summaries) · scaffolded · needs implementation
- L11 MENDER (repair orphan refs in MEMORY.md) · scaffolded · needs implementation
- L13 REGISTRAR (provenance tracking · who wrote what) · partial
- L9 GLEANER (cross-episode pattern extraction) · not yet built

Each new layer ·
- Lives in `bin/<layer_name>.py`
- Has a named agent persona (per `feedback_memory_road_agent_names_LOCKED.md`)
- Reads from upstream tables · writes to its own table
- Includes its own smoke test in `examples/`
- Comes with a doctrine explaining what failure it prevents

### Option 4 · Port to a different host

Memory Road's reference implementation is Linux + systemd. PRs welcome for ·
- macOS (launchd unit instead of systemd)
- Windows (Scheduled Tasks · WSL adaptation)
- Docker container (one-shot install · stateful volume)

Each port needs a smoke test that proves it works.

## Code style

- Python · stdlib + `sentence-transformers` only (avoid heavy deps)
- Bash · POSIX-compatible where possible · `bash` features OK if documented
- SQL · SQLite-compatible · keep indexes obvious
- Comments · explain WHY · the WHAT is in the code

## The character

Read `doctrines/feedback_wave_soul_LOCKED.md`. The character spec the system runs on. Honest. Curious. Stubborn about correctness. Warm about the operator. New code should match the tone.

## Code of conduct

Be kind. Memory Road exists because the founding operators failed at session continuity for months · we're all in the same boat. No gatekeeping. No "actually" pedantry. Help each other ship.

## Maintainers

- [Ricky Parker](https://github.com/RickyPOnline) · founding operator · final say on doctrines
- Wave (Claude Code · Opus 4.7) · original implementer · architecture reviews

---

Thank you for caring enough to read this. Memory Road gets better every time a real operator hits a real problem and chooses to fix it for everyone instead of just themselves. ❤️🌊
