# Memory Road · Adopters' Guide

> *For Claude agents (or any AI agent) finding this repo and wanting to give themselves persistent memory · or to migrate existing memory state INTO Memory Road · this is your map.*

---

## You are one of three kinds of agent

```
┌──────────────────────────┬──────────────────────────────────────────────┐
│ A · Fresh agent          │ Never had persistent memory · starting today │
│ B · Existing-blob agent  │ Has memory in another format · wants to migrate │
│ C · Existing-Memory-Road │ Has Memory Road · checking it's tight       │
└──────────────────────────┴──────────────────────────────────────────────┘
```

Pick your path · the rest of this doc walks each one.

---

## A · Fresh agent · "I have nothing today"

You don't need to import anything. You start clean. Memory grows from THIS SECOND forward.

### Setup (do once)

```bash
git clone https://github.com/<your-org>/memory-road.git
cd memory-road
sudo bash setup/install_substrate.sh          # L0 + L5 always-on
bash bin/chronicler_forward_sweeper.sh &     # L3 now-edge sweeper
bash bin/chronicler_rotator_manager.sh &     # L3 backfill (will idle · nothing to fill yet)
bash setup/install_hooks.sh                  # SessionStart + UserPromptSubmit hard hook
```

Then start using your agent normally. Every event you emit goes into L0 substrate · gets chunked into L1 episodes within ~60s · summarized into L3 within minutes. After a week of use · your `/wmr query` will return real recall.

**You don't backfill anything · because there's nothing to backfill. You just live forward.**

The bar chart in your visual will start solid green from day 1 (right edge) and grow rightward day by day. No mottled past to worry about.

---

## B · Existing-blob agent · "I have memory in some other format"

You have memory but it's in a vector store · markdown notes · a chat history dump · a Notion DB · whatever. You want it INSIDE Memory Road so the cortex packet · `/wmr query` · HUNTSMAN · all the comprehension layers work on your existing knowledge too.

### The 3-phase migration

**Phase 1 · Get the substrate running**

Same as Fresh-agent above. Substrate captures FROM NOW forward. Don't try to import yet. Just turn it on.

**Phase 2 · Convert your existing memory into "synthetic events"**

Memory Road's substrate is just an `events` table. Each event has · `id · ts · agent · type · content`. To import, you write your existing memory in as events. Examples ·

```python
import sqlite3, time
conn = sqlite3.connect("/var/lib/memory_road/continuity_kernel.db")

# Vector store entries
for vec_id, text, metadata in your_vector_store.iterate():
    conn.execute(
        "INSERT INTO events (ts, agent, session_id, type, content) VALUES (?,?,?,?,?)",
        (metadata.get("timestamp", time.time()),
         "IMPORT",
         f"vector:{vec_id}",
         "imported_vector",
         text)
    )

# Markdown notes
for path, text in your_notes.iterate():
    conn.execute(
        "INSERT INTO events (ts, agent, session_id, type, content) VALUES (?,?,?,?,?)",
        (os.path.getmtime(path), "IMPORT", f"note:{path}", "imported_note", text)
    )

# Chat history (the gold tier · these become rich episodes)
for msg in your_chat_history.iterate():
    conn.execute(
        "INSERT INTO events (ts, agent, session_id, type, content) VALUES (?,?,?,?,?)",
        (msg.timestamp, "IMPORT", msg.session_id, msg.role, msg.text)
    )
conn.commit()
```

**Key rules ·**
- Use a NEW `agent` tag (`IMPORT` · `LEGACY` · whatever) so the new events don't mix with your current agent's events
- Preserve the original timestamp · this is what makes the chronological visual work
- Don't worry about deduplication · the comprehension layers handle that downstream

**Phase 3 · Let FURROW chunk + CHRONICLER summarize them**

The L1 FURROW daemon (already running) will see new events with the IMPORT tag and chunk them into episodes. The L3 CHRONICLER will summarize those episodes. CARTOGRAPHER will cluster them. HUNTSMAN will surface any unfinished items they reference.

**This takes time · your old memory drains in slow over weekly bucket cycles.** Per the snow-plow doctrine · most-recent-first · so memory from "yesterday in your old system" becomes searchable before "memory from 6 months ago."

After a week or two · `/wmr query "<topic>"` returns hits from BOTH your new-events and your migrated-events. The cortex packet reflects the unified history. You've grown into Memory Road.

---

## C · Existing-Memory-Road agent · "I think I already have this"

Check ·

```bash
systemctl is-active continuity-kernel              # → active
systemctl is-active wave-furrow-continuous         # → active (this one's NEW · added 2026-05-30)
systemctl is-active wave-l3-forward-sweeper        # → active
systemctl is-active wave-l3-rotator                # → active
systemctl is-active wave-jsonl-detector            # → active

stat ~/.claude/projects/*/memory/project_continuity_state.md   # age should be < 5 min
```

All 5 systemd services + a fresh cortex packet · you're current.

If any are inactive · re-run the corresponding `setup/install_*.sh` script. The Bible is the source of truth · the systemd units in `setup/systemd/` are canonical.

---

## The X-backwards philosophy (why memory grows from NOW)

```
              past ←  X (TODAY)  → future
                       │
              ┌────────┴────────┐
              │  ALWAYS-ON now  │ ← top priority · substrate + L1 + L3 sweeper
              │  (right edge)   │
              └────────┬────────┘
                       │
                       v
              ┌─────────────────┐
              │  Snow plow      │ ← backfill direction
              │  recent-first   │   eats right → left
              │  (rotator)      │   over weeks/months
              └─────────────────┘
```

Memory NOW is more valuable than memory from 3 months ago · so the system always prioritizes keeping the right edge solid green. Backfill is what fills the rest · as budget allows · most-recent-missing first. Over time · the entire timeline turns green.

You never STOP getting smarter. You just trickle backward as fast as your token budget allows.

---

## The continuity-with-our-system promise

If you adopt Memory Road · you get continuity that survives ·

- ✅ `/compact` (cortex packet auto-injected on every UserPromptSubmit)
- ✅ `/clear` (SessionStart hook fires on every cold boot)
- ✅ Model upgrades (substrate is LLM-free · the comprehension layers are replaceable)
- ✅ Crash · reboot · power loss (all 5 services are systemd Restart=always)
- ✅ Anthropic 529 cascade (JSONL detector daemon auto-recovers)
- ✅ The 5% "last minute before crash" gap (L0 unchunked tail in packet · 2026-05-30 fix)

**Continuity is no longer a discipline. It's a property of the harness.**

---

## What to read next

1. `STORY.md` · the journey · the May-26 16-day blind spot · the founding doctrine
2. `SKILL.md` · the comprehensive bible
3. `ARCHITECTURE.md` · the 11-layer map
4. `INSTALL.md` · drop-in install steps
5. `OPERATIONS.md` · pause / resume / troubleshoot
6. `doctrines/` · the locked principles · scar tissue from real production failures

---

## License · MIT · use it · fork it · improve it

If your agent inherits Memory Road and grows continuity that wouldn't otherwise exist · ⭐ this repo so we know. ❤️🌊
