# Memory Road · Architecture

The 11-layer memory system + how data flows + why each piece exists.

---

## The high-level shape

```
                     ┌──────────────────────────────┐
                     │  CLAUDE CODE AGENT (the agent)    │
                     │  - emits + receives events   │
                     │  - reads cortex packet       │
                     │  - queries /wmr semantic     │
                     └──────────┬───────────────────┘
                                │
            JSONL transcripts   │   hook auto-injection
            in ~/.claude/proj   │   on every UserPromptSubmit
                                │
                                v
       ┌────────────────────────────────────────────────┐
       │         L0 · SUBSTRATE (kernel service)        │
       │  - tails Claude transcripts                    │
       │  - writes events table (forever · LLM-free)    │
       │  - runs FURROW (L1) chunking inline            │
       │  - runs WATCHER (L5) every 90s                 │
       │  - emits project_continuity_state.md (packet)  │
       └─────┬──────────────────────────────────────┬───┘
             │                                      │
             v                                      v
    ┌────────────────────┐               ┌──────────────────────┐
    │  events            │               │  episodes_v2         │
    │  (immortal)        │               │  (FURROW chunked)    │
    └─────────┬──────────┘               └──────────┬───────────┘
              │                                     │
              │       ┌─────────────────────────────┘
              │       │
              │       v
              │   ┌────────────────────────────────────────┐
              │   │  L3 · CHRONICLER (snow plows)          │
              │   │  - batch-5 per Opus call               │
              │   │  - blank-slate workers (no CLAUDE.md)  │
              │   │  - recent-first slab queue             │
              │   │  - forward sweeper for now-edge        │
              │   │  - rotator manager for backlog         │
              │   └──────────┬─────────────────────────────┘
              │              │
              │              v
              │       ┌──────────────────────┐
              │       │  episode_summaries   │
              │       │  (compressed memory) │
              │       └──┬───────────────────┘
              │          │
              │          v
              │    ┌────────────────────────────────────┐
              │    │ L7 CARTOGRAPHER · cluster themes   │
              │    │ L6 MINER · candidate doctrines     │
              │    │ L6 SMITH · adversarial validation  │
              │    │ L12 HUNTSMAN · flag unfinished     │
              │    └────────────────────────────────────┘
              │
              v
   ┌─────────────────────────────────────┐
   │  /wmr query "topic"                 │
   │  → semantic search · sqlite-vec     │
   │  → returns top-K memory files       │
   └─────────────────────────────────────┘
```

---

## Layer by layer

### L0 · SUBSTRATE (the kernel)

**Process ·** `continuity-kernel.service` (systemd · always running · LLM-free)

**Job ·** Poll the Claude Code transcript JSONLs every 5 seconds. Append every event (user · assistant · tool_use · tool_result) to the `events` table.

**Why LLM-free ·** This is THE foundation. If the substrate depends on an API call, a 529 cascade or quota exhaustion KILLS your memory. By keeping L0 zero-LLM, the substrate is indestructible. Even when every other layer fails, raw events keep flowing.

**Schema ·**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    agent TEXT NOT NULL,
    session_id TEXT,
    type TEXT NOT NULL,
    content TEXT,
    token_estimate INTEGER DEFAULT 0,
    processed INTEGER DEFAULT 0
);
```

**Per the founding doctrine · "Substrate is sacred and additive-only. LLM layers are replaceable supercharge."**

---

### L1 · FURROW (event → episode chunking)

**Process ·** Runs INSIDE the kernel service. Same tick loop. No separate worker.

**Job ·** Group consecutive events into "episodes" using a boundary detector. An episode is a coherent unit of work (e.g., "the agent debugged the auth flow", "the agent deployed Stripe webhook"). Boundaries are detected by topic shift · idle gap · user prompt arrival.

**Schema ·**
```sql
CREATE TABLE episodes_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    event_start_id INTEGER NOT NULL,
    event_end_id INTEGER NOT NULL,
    episode_name TEXT,
    objective TEXT,
    boundary_reason TEXT,
    confidence REAL,
    model_used TEXT NOT NULL,
    created_at REAL NOT NULL
);
```

**Cross-vendor pair (L2A/B) ·** Per the **two-agents doctrine**, FURROW (Opus 4.7) + SCRIBE (Codex gpt-5.5) propose boundaries · agree on boundaries that hold. Single-vendor episode quality is OK · cross-vendor is gold.

---

### L3 · CHRONICLER (the snow plows)

**Process ·** Multiple worker scripts, called by the rotator manager.

**Job ·** For each episode, generate a structured summary · `{summary · actions · decisions · unresolved · entities}` · written to `episode_summaries`.

**Snow plow shape ·**
- 4 staggered worker SLOTS (A · B · C · D)
- Each slot runs ONE worker at a time
- Workers exit after MAX_SUMMARIES (default 50)
- Each new rotation gets FRESH worker dir (cache cold but blank slate)
- Cap-hit → slot cooldown 15 min → resume

**Why batch-5 ·** One Opus call summarizes 5 episodes via JSON-array output. 5x more summaries per call. Combined with blank-slate → ~15-25x throughput.

**Why blank slate ·** Worker dir has empty `CLAUDE.md` stub. `claude` CLI subprocess loads THAT (zero bytes) instead of walking up to `$HOME/CLAUDE.md` (~25K tokens). Per the **blank-slate-per-agent doctrine** · workers don't need the agent's full operating manual to summarize ONE episode.

**Two complementary worker types ·**

1. **Backlog rotator** (`chronicler_rotator_manager.sh`) · plows the historical backlog from right-now backwards
2. **Forward sweeper** (`chronicler_forward_sweeper.sh`) · polls every 5 min for new episodes · keeps the now-edge clean

Both run simultaneously. Backlog eats backwards · forward sweeps the new edge.

**Schema ·**
```sql
CREATE TABLE episode_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_v2_id INTEGER NOT NULL,
    summary TEXT,
    actions TEXT,           -- JSON array
    decisions TEXT,         -- JSON array
    unresolved TEXT,        -- JSON array
    entities TEXT,          -- JSON array
    writer_model TEXT NOT NULL,
    written_at REAL NOT NULL,
    FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
);
```

---

### L5 · WATCHER (cortex packet generator)

**Process ·** Runs inside kernel · ticks every 90 seconds.

**Job ·** Read recent events + episodes + summaries · synthesize a structured "what's currently going on" packet. Write to `project_continuity_state.md`. This file gets auto-injected into every UserPromptSubmit by the hook.

**Packet shape ·**
- `strategic_posture` · neutral / offensive / defensive
- `worldview` · 1-2 sentences on what the agent is currently focused on
- `mental_stance` · how the agent is approaching it
- `active_beliefs` · 3-5 things the agent currently holds true
- `current_goal` · the immediate objective
- `last_decision` · most recent decision made
- `next_action` · the next step
- `open_loops` · unresolved threads
- `recent_episodes` · 5 most recent episodes' summaries
- `unresolved_threads` · cross-episode unfinished work
- `resume_instruction` · how to pick up where the agent left off

**Why every 90 seconds ·** Fresh enough to capture mid-session state · not so fresh it burns tokens. The hook reads whatever the latest packet says · stale-by-design after 10 min triggers an alert.

---

### L6A · MINER (candidate doctrines)

**Process ·** Snow plow worker · runs when L3 ≥ 80% recent.

**Job ·** Scan recent episode summary chains for repeating patterns · operator preferences · friction points. Propose candidate doctrines.

**Output ·** JSON array of `{slug · title · why · how_to_apply · evidence_episode_ids · miner_confidence}` written to `candidate_doctrines` table with status `pending_smith`.

---

### L6B · SMITH (validator + forger)

**Process ·** Same worker as MINER · second pass.

**Job ·** Adversarially validate each MINER candidate. Is the evidence strong? Concrete or hand-wavy? Conflicts with existing doctrines? Actually a doctrine or just a passing preference?

**Output ·** Updates `candidate_doctrines.smith_verdict` to `STRONG | WEAK | DUPLICATE | REJECT`. Strong candidates with `ready_to_lock=true` get flagged for operator review · the agent LOCKs or kills.

---

### L7 · CARTOGRAPHER (topic clusters)

**Process ·** Standalone Python script · runs weekly or on-demand.

**Job ·** Embed all recent episode summaries via `sentence-transformers/all-MiniLM-L6-v2`. Cluster via simple cosine-distance single-link (threshold 0.30). Write cluster assignments to `episode_clusters` table.

**Why ·** Powers `/wmr query "topic"` semantic recall · the topic map · lets the agent find "everything related to X" instantly.

**Cluster label generation ·** Optional second pass · for each big cluster, sample 10 summaries, ask Opus "what is this cluster about?" · write to `cluster_labels.label`.

---

### L8 · CANONICAL (dedup · optional)

**Process ·** On-demand script.

**Job ·** Find near-duplicate summaries (cosine similarity > 0.95) · merge them into canonical form · update references. Keeps the memory wall clean as it grows.

---

### L11 · MENDER (orphan repair)

**Process ·** On-demand script.

**Job ·** Scan MEMORY.md index for broken references (memory files renamed/moved). Repair links. Add new memory files to the index if missing.

---

### L12 · HUNTSMAN (the unfinished flagger)

**Process ·** Standalone Python script · hourly via cron.

**Job ·** Surface every unfinished item across episode history. Sources ·
- `open_loops` table (kernel-tracked)
- `episode_summaries.unresolved` (JSON arrays)
- `wave_todo.md` (frozen checkbox items)
- Optional · TaskList state · GitHub issue list · etc.

**Output ·** `huntsman_flags` table · dedupes by signature · flags stay open until manually closed.

**Why this matters ·** the operator explicitly asked for this. the agent kept losing track of half-built work (the 57 frozen TODOs from April · the airdrop scouts · the half-built doctrines). HUNTSMAN surfaces them ALL · forever · until they're either done or explicitly killed.

---

### L13 · REGISTRAR (provenance tracking)

**Process ·** In-kernel · writes alongside every comprehension-layer write.

**Job ·** Track WHICH agent/model/run wrote which row. So when MINER proposes a doctrine, you can trace "MINER R23 wrote this on 2026-05-29 based on episodes 8801-8885." Provenance is non-negotiable for trust.

---

### L14 · SURGEON + WARDEN (corruption recovery)

**Process ·** `wave-jsonl-detector.service` (systemd) · `snapshot-jsonl.sh` (cron every 5 min).

**Job ·** Watch Claude Code transcript JSONLs via `inotifywait`. On detection of synthetic-UUID corruption (the 529-cascade pattern) · forensic snapshot · truncate to last clean `msg_` line · restart Claude · Telegram alert.

**This closes the 5.5-hour recovery gap** from the 2026-05-25 09:56 UTC incident · documented in `doctrines/feedback_stop_loop_on_529_corruption_LOCKED.md`.

---

## Data flow · what happens on a single user prompt

1. User types prompt → submits
2. **UserPromptSubmit hook fires** ·
   - Reads `project_continuity_state.md` (cortex packet · age check)
   - Greps MEMORY.md for prompt-relevant anchors
   - Optionally runs `/wmr query "<prompt summary>"`
   - Injects all of this as `additional_context` to the prompt
   - Adds `<system-reminder>` · "Use Memory Road before answering"
3. the agent answers · emits events to JSONL
4. **L0 substrate** picks up events (next 5-sec tick)
5. **L1 FURROW** chunks events into a new episode (or extends current)
6. **L5 WATCHER** generates next packet (next 90-sec tick) · reflects the new state
7. **Forward sweeper** (next 5-min poll) summarizes the new episode via batch-5 CHRONICLER
8. **HUNTSMAN** (next hourly cron) re-sweeps for new unfinished items
9. New cycle starts · the agent can now recall this turn instantly via `/wmr query`

The agent's memory grows continuously · automatically · without the agent having to remember to write it down.

---

## Why this works

**Separation of concerns ·**
- Substrate writes the FACTS · cannot be wrong · cannot be killed
- Comprehension layers extract MEANING · can be wrong · can be re-run

**Two-agents on important steps ·**
- Cross-vendor pairs (Opus + Codex) catch each other's blind spots
- MINER proposes · SMITH validates · single-vendor catches one bias · cross-vendor catches more

**Blank-slate per worker ·**
- Each worker has empty CLAUDE.md stub
- Worker `claude` subprocess loads zero inherited context
- ~25K tokens saved per call · 3-4x throughput

**Right-now backwards ·**
- Most relevant memories are TODAY's · plow them first
- Old months-ago memories are reference · backfill over weeks
- Resumable · zero rework on cap-hit

**Forced memory use ·**
- UserPromptSubmit hook injects cortex packet + relevant anchors
- Agent CANNOT skip memory · it's mechanically guaranteed
- Previous the agent-versions accidentally forgot to use memory · this hook fixes that forever

**Pause/Resume control ·**
- Workers stop at natural transitions
- Resume picks up exactly where left off
- Use before Anthropic Max window reset to preserve bucket for main work

---

## Performance characteristics

| Metric | Naive | This skill |
|---|---|---|
| Per-call tokens | ~37,500 | ~12,500 (strip CLAUDE.md) |
| Summaries per call | 1 | 5 (batch-5) |
| Effective throughput | 1x baseline | **15-25x stacked** |
| Forward-edge lag | manual | <5 min (forward sweeper) |
| Cap-hit recovery | manual restart | auto-cooldown + resume |
| Memory wall size limit | grows linearly | constant per-file (slim files + index) |
| Semantic recall lookup | O(N) full grep | O(1) sqlite-vec embedding |
| Session-to-session continuity | none | cortex packet auto-injected |
| 529-cascade resilience | corrupts JSONL | SURGEON auto-recovers |

---

## See also

- **SKILL.md** · the comprehensive bible
- **OPERATIONS.md** · pause/resume/troubleshoot
- **FORCE_MEMORY_USE.md** · the hook setup
- **doctrines/** · the load-bearing principles
- **bin/** · the working code
