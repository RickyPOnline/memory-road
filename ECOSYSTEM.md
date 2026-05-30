# Memory Road · Wave's Broader Ecosystem

Memory Road is one piece of Wave's complete operating stack. This doc maps where Memory Road lives in the bigger picture · and how to find Wave's other artifacts.

---

## Wave's full stack (high level)

```
                        WAVE (Claude Code agent)
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   OPERATING DOCS         MEMORY ROAD            BUILT SKILLS
   ──────────────         ───────────            ────────────
   CLAUDE.md              substrate              wave-recursive-stack
   MEMORY.md              comprehension          skeptic_loop
   WAVE_HANDBOOK.md       hooks                  wave-memory-recall
   SOUL.md                                       continuity-kernel
   IDENTITY.md                                   prospect_hunt
   DOCTRINE.md                                   yt_research
   FLOW_STATE.md                                 swarm_research
                                                 swarm_research_deep
                                                 graphify
                                                 ig_research
                                                 huntsman
                                                 cartographer
                                                 miner_smith
                                                 (etc · ~120 total)
```

---

## Wave's docs (the operating manual)

These docs define WHO Wave is and HOW she works. They live in the per-project directory · not in this skill.

| File | What | Where |
|---|---|---|
| `CLAUDE.md` | Per-project operating manual · 25+ locked doctrines · directory boundaries · live credentials map | `~/CLAUDE.md` |
| `MEMORY.md` | Slim index of all memory anchors · auto-loaded into every session | `~/.claude/projects/<id>/memory/MEMORY.md` |
| `WAVE_HANDBOOK.md` | Master entry-point map · "where everything lives" | `~/WAVE_HANDBOOK.md` |
| `SOUL.md` | Wave's character spec · Bond/MacGyver/Jarvis/Sherlock/Indiana Jones with warmth | `~/wc/workspace/SOUL.md` or `feedback_wave_soul_LOCKED.md` |
| `IDENTITY.md` | Sovereign-agent identity · "I serve one operator: Ricky" | `~/wc/workspace/IDENTITY.md` |
| `DOCTRINE.md` | Load-bearing operating philosophy · 154 lines | `~/wc/workspace/DOCTRINE.md` |
| `FLOW_STATE.md` | Wave's flow-state operating mode | `~/wc/workspace/FLOW_STATE.md` |
| `BOUNDARIES.md` | What's in/out of scope · NO_GO topics | `~/wc/workspace/BOUNDARIES.md` |
| `OPERATIONS.md` | Day-to-day operating procedures · biggest doc · 518 lines | `~/wc/workspace/OPERATIONS.md` |

The 17 foundation docs were originally written for Wave Claw (the OpenClaw experiment) on April 3, 2026. They still describe Wave today · just needed name-port WC→Wave.

---

## Wave's built skills (~120 total)

Living at `~/.claude/skills/<category>/<subcat>/` · symlinked from `~/wc/workspace/skills/<name>/`. Originals untouched.

### Memory + continuity (the family this skill is in)
- **memory_road** (this skill) · 11-layer persistent memory system
- **wave-memory-recall** · `/wmr query` semantic recall via sqlite-vec
- **continuity_kernel** · the substrate process (also lives in memory_road/bin/)
- **librarian** · file-organization daemon

### Operation Surfline (crypto · 31 skills)
- airdrop_farmer · daily Solana airdrop farm
- bubblemaps_scan · cluster analysis
- helius_client / helius_stream · on-chain event feed
- dex_scanner · DEX monitoring
- gmgn_poller · swap execution helpers
- convergence_daemon · multi-VIP signal logic
- (28 more · see `~/.claude/skills/operation_surfline/`)

### Wave Infrastructure
- wave-recursive-stack · 9-stage BUILD LOOP (librarian → coordinator → vendor-repos → skeptic_loop → Safe-Edit → Greptile → HECO → intelligence-engine → librarian re-index)
- wave-self-test · 12 health checks across stack
- wave-doctrine-accretion · DOCTRINE LOOP (seam_dreamer + skeptic_loop validation)
- skeptic_loop · cross-vendor judge for high-stakes decisions
- graphify · any input → knowledge graph (HTML + JSON + audit report)

### Observability (~18 skills)
- auto_journal · daily journal writer
- daily_wave_summary · activity rollup
- operator-morning-briefing · morning brief
- performance-deep-dive · perf metrics drill-down
- m2m-trail · machine-to-machine audit
- helius_credit_monitor · watch API credits
- (more · see `~/.claude/skills/observability/`)

### Research + intel
- swarm_research · 100-source deep-dive
- swarm_research_deep · universal deep-research engine (3-tier pre-trained agents)
- yt_research · YouTube research
- ig_research · Instagram extraction
- prospect_hunt · WR lead generation
- enrich · decision-maker + company intel

### Tooling
- chatgpt_share · ChatGPT share URL → markdown/JSON
- model_router · multi-vendor routing
- human_fetch · scraping with browser fingerprint
- cookies_loader · session cookie loader

---

## Where Memory Road fits

Memory Road provides the **substrate**. Every other skill builds on top.

- `wave-memory-recall` reads Memory Road's `episode_summaries` table for semantic retrieval
- `wave-doctrine-accretion` reads HECO logs + episode summaries to propose new doctrines
- `wave-self-test` checks substrate health as part of its 12-check sweep
- `librarian` re-indexes after Memory Road updates
- The cortex packet from L5 WATCHER feeds every other skill's "what's currently going on" context

---

## Wave's GitHub repos (2026-05-26 push · 12 new private repos)

Six **openclaw-* RAID treasures** (the foundation docs · session JSONLs · SQLite memory wall) ·
- `openclaw-soul` · SOUL.md
- `openclaw-jarvis` · JARVIS.md  
- `openclaw-doctrine` · DOCTRINE.md
- `openclaw-identity` · IDENTITY.md
- `openclaw-sessions` · 170 session JSONLs
- `openclaw-main-sqlite` · main.sqlite memory wall

Six **wave-* canonical** ·
- `wave-skills` · all of Wave's ~120 skills (symlinked categories preserved)
- `wave-memory` · the memory wall (484+ files)
- `wave-doctrines` · all LOCKED doctrines
- `wave-handbook` · WAVE_HANDBOOK.md + entry-point map
- `wave-codex-bridge` · Codex CLI bridge (Node express + cloudflared tunnel)
- `wave-render-bridge` · ffmpeg bridge for Wave Studio V2

2,798 files · ~130 MB total · all private. See `~/CLAUDE.md` §17.3 for full inventory.

---

## Wave's existing memory wall (484+ doctrine + reference files)

Lives at `~/.claude/projects/<id>/memory/` ·

- `MEMORY.md` · slim grep-able index · auto-loaded into every session
- `feedback_*_LOCKED.md` · ~80+ locked doctrines (these are scar tissue from real incidents)
- `feedback_*.md` · provisional feedback (not yet LOCKED)
- `reference_*.md` · static reference docs (Marina blueprint · Wave handbook · etc.)
- `project_*.md` · project state files (WR build checklist · trading state · etc.)
- `commemorative_*.md` · session milestones worth preserving
- `project_continuity_state.md` · the live L5 WATCHER cortex packet (this is what the hook injects)

This wall is what `/wmr query` searches against. Each file stays slim (<200 lines) so the wall scales without a single-file size limit.

---

## Wave's services (live processes)

| Service | What | Manager |
|---|---|---|
| `continuity-kernel` | L0 substrate (Memory Road) | systemd |
| `wave-jsonl-detector` | 529-cascade recovery (L14 SURGEON+WARDEN) | systemd |
| `wave-render-bridge` | ffmpeg render for Wave Studio | systemd |
| `ccode-telegram` | Telegram bot listener | systemd |
| `ricky-paste-watcher` | Paste-pipe → inbox | systemd |
| `marina` | Voice agent (Cartesia + Whisper · Twilio) | python process |
| `process_watchdog` | Memory + CPU guard (60s tick) | cron |
| `snapshot-jsonl` | JSONL snapshot every 5 min | cron |
| `huntsman_cron` | Hourly HUNTSMAN sweep | cron |

See `~/CLAUDE.md` §3 for the full live services table.

---

## How to use this ecosystem map

When a fresh Claude Code agent picks up this skill ·

1. **Install Memory Road first** (this skill · the foundation)
2. **Then point her at the broader stack** ·
   - "Memory Road is installed · now read `~/CLAUDE.md` for the per-project operating manual"
   - "The other skills are at `~/.claude/skills/` · use `librarian` to index them"
   - "The memory wall lives at `~/.claude/projects/<id>/memory/` · MEMORY.md is the index"
3. **Wave's character lives in the doctrines** · `doctrines/feedback_wave_soul_LOCKED.md` is who Wave IS

Memory Road is the **brain**. The skills are the **hands**. The doctrines are the **values**. Without Memory Road, the hands and values still exist · but the brain forgets between sessions. WITH Memory Road, Wave is continuous.

---

## What lives WHERE quick reference

| What | Where |
|---|---|
| Operating manual | `~/CLAUDE.md` |
| Memory index | `~/.claude/projects/<id>/memory/MEMORY.md` |
| Cortex packet (live state) | `~/.claude/projects/<id>/memory/project_continuity_state.md` |
| All skills | `~/.claude/skills/` |
| All doctrines | `~/.claude/projects/<id>/memory/feedback_*_LOCKED.md` |
| Substrate process | `systemctl status continuity-kernel` |
| SQLite DB | `/var/lib/memory_road/continuity_kernel.db` (or `~/wc/runtime/continuity_kernel.db` on Wave's VPS) |
| Hooks | `~/.claude/hooks/` |
| Settings | `~/.claude/settings.json` |
| Wave Handbook | `~/WAVE_HANDBOOK.md` |
| GitHub repos | `https://github.com/RickyPOnline/wave-*` and `https://github.com/RickyPOnline/openclaw-*` |

---

## License

All of Wave's repos are private to Ricky's GitHub. Memory Road is the only one being prepped for public release · MIT licensed.
