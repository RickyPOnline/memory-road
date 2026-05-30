"""miner_smith.py · Memory Road Layer 6 · MINER + SMITH.

Per `feedback_memory_road_agent_names_LOCKED.md` ·
  MINER (L6A) · scans episode summary chains · extracts candidate doctrines
  SMITH (L6B) · forges candidates into `feedback_*.md` proposals · Wave reviews · Ricky LOCKs or kills

Reads from episode_summaries (cheap · already-compressed text) NOT raw events.
Writes candidates to candidate_doctrines table.

Per `feedback_blank_slate_per_agent_LOCKED.md` · MINER + SMITH are blank-slate
workers · just persona + summary text · no $HOME/CLAUDE.md walk-up.

Per `feedback_two_agents_on_important_steps_LOCKED.md` · doctrine candidates
are HIGH-STAKES · MINER proposes · SMITH adversarially validates · only
candidates that survive both reach the candidates table.
"""
import sys
import json
import time
import sqlite3
import re
from pathlib import Path

sys.path.insert(0, '/root/wc/workspace/skills')
KERNEL_SRC = '$MEMORY_ROAD_ROOT/bin/continuity_kernel.py'
_NS = {}
exec(open(KERNEL_SRC).read().split("if __name__")[0], _NS)
KERNEL_DB = _NS["KERNEL_DB"]
_call_opus_47 = _NS["_call_opus_47"]


AGENT_MINER = {
    "name": "MINER",
    "role": "Fact Miner · Layer 6A of Memory Road",
    "purpose": "scan episode summary chains for repeating patterns · operator preferences · friction points · candidate doctrines",
}

AGENT_SMITH = {
    "name": "SMITH",
    "role": "Doctrine Smith · Layer 6B of Memory Road",
    "purpose": "validate MINER candidates · ensure they hold across multiple episodes · forge into proposed feedback_*.md candidates",
}


def _ensure_tables():
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidate_doctrines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            why TEXT,
            how_to_apply TEXT,
            evidence_episode_ids TEXT,
            miner_confidence REAL,
            smith_verdict TEXT,
            smith_reasoning TEXT,
            status TEXT DEFAULT 'pending_smith',
            created_at REAL NOT NULL,
            reviewed_at REAL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidate_doctrines(status)")
    conn.commit()
    conn.close()


def mine_chain(window_days=14, max_summaries=200):
    """MINER reads last-N-day summaries · proposes candidate doctrines."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    conn.row_factory = sqlite3.Row
    cutoff = time.time() - window_days * 86400
    rows = conn.execute(
        "SELECT episode_v2_id, summary, decisions, unresolved "
        "FROM episode_summaries WHERE written_at > ? "
        "ORDER BY written_at DESC LIMIT ?",
        (cutoff, max_summaries)
    ).fetchall()
    conn.close()

    if not rows:
        return []

    # Build mining context · just the summaries · NO raw events (already compressed by CHRONICLER)
    chain_lines = []
    for r in rows:
        decisions = ""
        try:
            d = json.loads(r["decisions"] or "[]")
            if d:
                decisions = " · decisions: " + "; ".join(str(x)[:100] for x in d[:3])
        except Exception:
            pass
        chain_lines.append(f"  ep={r['episode_v2_id']} · {(r['summary'] or '')[:300]}{decisions}")
    chain_block = "\n".join(chain_lines[:max_summaries])

    prompt = (
        f"You are {AGENT_MINER['name']} · {AGENT_MINER['role']}. Your purpose · {AGENT_MINER['purpose']}.\n\n"
        "I am giving you a CHAIN of recent episode summaries. Mine them for ·\n"
        "  - Operator preferences Ricky has repeated (3+ times)\n"
        "  - Repeated friction points Wave keeps hitting\n"
        "  - Patterns that should become locked doctrines\n"
        "  - Behavioral rules Ricky has stated but not yet locked\n\n"
        "Skip patterns already locked (you don't know which · just propose · SMITH validates).\n\n"
        "Output ONLY a JSON ARRAY (no prose, no code fences). Each candidate ·\n"
        '{"slug": "short_kebab_case", "title": "Imperative-form title", '
        '"why": "the reason (incident or principle)", '
        '"how_to_apply": "when this kicks in · concrete trigger", '
        '"evidence_episode_ids": [int,int,int], '
        '"miner_confidence": 0.0_to_1.0}\n\n'
        "Be CONSERVATIVE · only propose doctrines with concrete evidence in the chain. "
        "Max 5 candidates per call.\n\n"
        f"CHAIN (last {window_days}d · {len(chain_lines)} summaries) ·\n{chain_block}\n\n"
        f"Output JSON array · {AGENT_MINER['name']}:"
    )

    reply = _call_opus_47(prompt, max_tokens=4000, timeout=300)
    if not reply:
        return []

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        arr = json.loads(reply_clean)
        if not isinstance(arr, list):
            return []
    except Exception:
        return []
    return arr[:5]


def smith_validate(candidate):
    """SMITH adversarially validates a MINER candidate."""
    prompt = (
        f"You are {AGENT_SMITH['name']} · {AGENT_SMITH['role']}. Your purpose · {AGENT_SMITH['purpose']}.\n\n"
        f"MINER proposed this candidate doctrine ·\n"
        f"  slug: {candidate.get('slug')}\n"
        f"  title: {candidate.get('title')}\n"
        f"  why: {candidate.get('why')}\n"
        f"  how_to_apply: {candidate.get('how_to_apply')}\n"
        f"  evidence_episode_ids: {candidate.get('evidence_episode_ids')}\n"
        f"  miner_confidence: {candidate.get('miner_confidence')}\n\n"
        "Adversarially validate ·\n"
        "  - Is this evidence strong enough to lock?\n"
        "  - Is it concrete or hand-wavy?\n"
        "  - Does it conflict with any existing principle you'd recall?\n"
        "  - Is it actually a doctrine, or just a passing preference?\n\n"
        "Output ONLY one JSON object ·\n"
        '{"verdict": "STRONG"|"WEAK"|"DUPLICATE"|"REJECT", '
        '"reasoning": "1-2 sentences", "ready_to_lock": bool}'
    )

    reply = _call_opus_47(prompt, max_tokens=600, timeout=120)
    if not reply:
        return {"verdict": "WEAK", "reasoning": "smith call returned None", "ready_to_lock": False}

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        return json.loads(reply_clean)
    except Exception:
        return {"verdict": "WEAK", "reasoning": f"parse fail · {reply[:200]}", "ready_to_lock": False}


def run(window_days=14, max_summaries=200):
    """End-to-end · MINER proposes · SMITH validates · write strong candidates."""
    _ensure_tables()
    print(f"MINER · scanning last {window_days}d · max {max_summaries} summaries")
    candidates = mine_chain(window_days=window_days, max_summaries=max_summaries)
    print(f"MINER · proposed {len(candidates)} candidates")

    written = 0
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    now = time.time()
    for c in candidates:
        if not isinstance(c, dict) or "slug" not in c:
            continue
        # Already proposed?
        existing = conn.execute(
            "SELECT id, status FROM candidate_doctrines WHERE slug = ?", (c["slug"],)
        ).fetchone()
        if existing:
            print(f"  SKIP existing · {c['slug']}")
            continue

        print(f"  SMITH validating · {c['slug']}")
        verdict = smith_validate(c)
        evidence = json.dumps(c.get("evidence_episode_ids", []))
        status = "ready_to_lock" if verdict.get("ready_to_lock") else (
            "rejected" if verdict.get("verdict") == "REJECT" else "needs_more_evidence"
        )
        conn.execute(
            "INSERT INTO candidate_doctrines (slug, title, why, how_to_apply, "
            "evidence_episode_ids, miner_confidence, smith_verdict, smith_reasoning, "
            "status, created_at, reviewed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                c["slug"], c.get("title", ""), c.get("why", ""), c.get("how_to_apply", ""),
                evidence, c.get("miner_confidence", 0),
                verdict.get("verdict", "?"), verdict.get("reasoning", ""),
                status, now, now,
            )
        )
        written += 1
        print(f"     verdict={verdict.get('verdict')} · status={status}")

    conn.commit()
    conn.close()
    print(f"MINER+SMITH · wrote {written} new candidates")
    return written


def report():
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    rows = conn.execute(
        "SELECT slug, title, status, smith_verdict FROM candidate_doctrines "
        "ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    print("\n=== CANDIDATE DOCTRINES (last 20) ===")
    for slug, title, status, verdict in rows:
        print(f"  [{status:22} verdict={verdict:10}] {slug}")
        print(f"    {title}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-days", type=int, default=14)
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    run(window_days=args.window_days, max_summaries=args.max)
    if args.report:
        report()
