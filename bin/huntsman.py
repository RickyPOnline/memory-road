"""huntsman.py · Memory Road Layer 12 · HUNTSMAN.

Per `feedback_memory_road_agent_names_LOCKED.md` · HUNTSMAN flags every
unfinished item across episode history · "the one the operator asked for."

Surfaces ·
  - Open loops from kernel's open_loops table
  - Unresolved threads from episode_summaries.unresolved (JSON array column)
  - Pending TODOs from wave_todo.md (the April-20 frozen 57 items)
  - Pending tasks from TaskList state where they exist

Writes to huntsman_flags table · idempotent · dedupes by signature.

Runs EARLY · doesn't wait for L3 to be at 100% · scans whatever exists +
keeps re-scanning every hour to surface new unfinished items as L3 grows.

Per `feedback_blank_slate_per_agent_LOCKED.md` · HUNTSMAN is its own
focused worker · ONLY job is flagging unfinished items.
"""
import sys
import json
import time
import sqlite3
import hashlib
import re
from pathlib import Path

sys.path.insert(0, '/root/wc/workspace/skills')
KERNEL_SRC = '$MEMORY_ROAD_ROOT/bin/continuity_kernel.py'

_NS = {}
exec(open(KERNEL_SRC).read().split("if __name__")[0], _NS)
KERNEL_DB = _NS["KERNEL_DB"]


def _ensure_table():
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS huntsman_flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signature TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            source_ref TEXT,
            kind TEXT NOT NULL,
            description TEXT NOT NULL,
            first_seen REAL NOT NULL,
            last_seen REAL NOT NULL,
            status TEXT DEFAULT 'open',
            closed_at REAL,
            closure_reason TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_huntsman_status ON huntsman_flags(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_huntsman_source ON huntsman_flags(source)")
    conn.commit()
    conn.close()


def _sig(*parts):
    h = hashlib.sha256("|".join(str(p)[:300] for p in parts).encode()).hexdigest()[:16]
    return h


def _upsert(conn, signature, source, source_ref, kind, description):
    now = time.time()
    existing = conn.execute(
        "SELECT id, status FROM huntsman_flags WHERE signature = ?", (signature,)
    ).fetchone()
    if existing:
        # Update last_seen
        conn.execute(
            "UPDATE huntsman_flags SET last_seen = ? WHERE id = ?",
            (now, existing[0])
        )
        return False  # already known
    conn.execute(
        "INSERT INTO huntsman_flags (signature, source, source_ref, kind, description, first_seen, last_seen) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (signature, source, source_ref, kind, description[:1500], now, now)
    )
    return True


def sweep_open_loops():
    """Scan kernel's open_loops table for entries still open."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    new_count = 0
    try:
        rows = conn.execute(
            "SELECT id, description, still_open FROM open_loops WHERE still_open = 1"
        ).fetchall()
    except sqlite3.OperationalError:
        # open_loops table or columns might not exist · skip silently
        rows = []

    for r in rows:
        loop_id, desc, _open = r
        if not desc:
            continue
        sig = _sig("open_loop", loop_id, desc[:100])
        if _upsert(conn, sig, "open_loops", str(loop_id), "open_loop", desc):
            new_count += 1
    conn.commit()
    conn.close()
    return new_count


def sweep_episode_unresolved(min_recent_days=30):
    """Scan episode_summaries.unresolved for unfinished threads · recent first."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    new_count = 0
    cutoff = time.time() - (min_recent_days * 86400)
    rows = conn.execute(
        "SELECT episode_v2_id, unresolved FROM episode_summaries "
        "WHERE written_at > ? AND unresolved IS NOT NULL AND unresolved != '[]'",
        (cutoff,)
    ).fetchall()

    for ep_id, unresolved_json in rows:
        try:
            unresolved = json.loads(unresolved_json)
        except Exception:
            continue
        for item in unresolved[:5]:
            item_text = str(item)[:300]
            if not item_text:
                continue
            sig = _sig("episode_unresolved", ep_id, item_text[:100])
            if _upsert(conn, sig, "episode_summaries.unresolved", str(ep_id),
                       "unresolved_thread", item_text):
                new_count += 1
    conn.commit()
    conn.close()
    return new_count


def sweep_wave_todo_md(path="$HOME/.memory_road/runtime/wave_todo.md"):
    """Scan the frozen wave_todo.md (April-20 era) for the 57 unfinished items."""
    p = Path(path)
    if not p.exists():
        return 0
    new_count = 0
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    text = p.read_text(errors="ignore")
    # Look for checkbox-style items · `- [ ]` or `* [ ]`
    items = re.findall(r"^[-*]\s*\[\s\]\s*(.+)$", text, re.MULTILINE)
    for item in items:
        item = item.strip()[:500]
        if not item:
            continue
        sig = _sig("wave_todo_md", item[:100])
        if _upsert(conn, sig, "wave_todo.md", "frozen-2026-04-20",
                   "frozen_todo", item):
            new_count += 1
    conn.commit()
    conn.close()
    return new_count


def report(top_n=20):
    """Print the top-N most-recently-seen open flags."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    rows = conn.execute(
        "SELECT kind, source, source_ref, description "
        "FROM huntsman_flags WHERE status = 'open' "
        "ORDER BY last_seen DESC LIMIT ?", (top_n,)
    ).fetchall()
    counts = conn.execute(
        "SELECT kind, COUNT(*) FROM huntsman_flags WHERE status = 'open' GROUP BY kind"
    ).fetchall()
    conn.close()

    print(f"\n=== HUNTSMAN REPORT · top {top_n} open flags ===\n")
    for kind, source, ref, desc in rows:
        print(f"  [{kind:18}] {source}:{ref or '-'}")
        print(f"     {desc[:200]}")
    print(f"\n=== COUNTS BY KIND ===")
    for kind, n in counts:
        print(f"  {kind:18} · {n}")


def full_sweep():
    """Run all sweepers · idempotent · safe to re-run."""
    _ensure_table()
    new_loops = sweep_open_loops()
    new_unresolved = sweep_episode_unresolved()
    new_frozen = sweep_wave_todo_md()
    total_new = new_loops + new_unresolved + new_frozen
    print(f"HUNTSMAN sweep · new_open_loops={new_loops} new_unresolved={new_unresolved} new_frozen_todos={new_frozen} · total_new={total_new}")
    return total_new


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="show open flags report")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    full_sweep()
    if args.report:
        report(args.top)
