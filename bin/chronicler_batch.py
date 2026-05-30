"""chronicler_batch.py · Batch summarization for Memory Road Layer 3 CHRONICLER.

Per `feedback_blank_slate_per_agent_LOCKED.md` and
    `feedback_strip_claude_md_from_worker_dirs_LOCKED.md` and
    `feedback_snow_plow_pattern_right_now_backward_LOCKED.md`.

Stacks 5x throughput on top of CLAUDE.md-strip · ~15-25x stacked vs raw.

Caller protocol ·
  1. Worker dir has empty CLAUDE.md stub · subprocess `claude` doesn't walk up
  2. Worker imports this module · calls `summarize_batch(episode_ids)`
  3. Returns list of successfully-summarized IDs
  4. Failed IDs can be re-queued for single-fire fallback

DO NOT MODIFY continuity_kernel.py · this is a sidecar.
"""
import sys
import json
import re
import time
import sqlite3
from pathlib import Path

sys.path.insert(0, '/root/wc/workspace/skills')
KERNEL_SRC = '$MEMORY_ROAD_ROOT/bin/continuity_kernel.py'

# Import what we need from the live kernel WITHOUT running its main loop
_NS = {}
exec(open(KERNEL_SRC).read().split("if __name__")[0], _NS)
KERNEL_DB = _NS["KERNEL_DB"]
AGENT_CHRONICLER = _NS["AGENT_CHRONICLER"]
_call_opus_47 = _NS["_call_opus_47"]
summarize_layer4_chronicler = _NS["summarize_layer4_chronicler"]
_log = _NS.get("_log", lambda m: None)


def _build_event_block(events, max_chars=300):
    """Compress events into a single text block · trim ANSI noise."""
    lines = []
    for r in events:
        c = (r["content"] or "")[:max_chars].replace("\n", " ")
        lines.append(f"  id={r['id']} type={r['type']}  {c}")
    return "\n".join(lines)


def _arr(v):
    if isinstance(v, list):
        return json.dumps([str(x)[:400] for x in v[:30]])
    if isinstance(v, str):
        return json.dumps([v[:400]])
    return json.dumps([])


def summarize_batch(episode_ids, max_tokens_per_call=12000, timeout=240, batch_writer_model="claude-opus-4-7-CHRONICLER-BATCH"):
    """Batch CHRONICLER · 5 episodes per Opus call.

    Args:
        episode_ids · list of int episode_v2 IDs (recommend 3-5 per batch)
        max_tokens_per_call · output token budget · need ~2500 per episode
        timeout · seconds for the Opus call
        batch_writer_model · what gets written to episode_summaries.writer_model

    Returns:
        dict · {'ok': [ep_ids_written], 'fail': [ep_ids_unwritten], 'reason': str_or_None}
    """
    if not episode_ids:
        return {"ok": [], "fail": [], "reason": "empty"}

    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    conn.row_factory = sqlite3.Row

    # Pull all episodes + their events in 2 queries
    placeholders = ",".join("?" * len(episode_ids))
    ep_rows = conn.execute(
        f"SELECT * FROM episodes_v2 WHERE id IN ({placeholders}) ORDER BY id ASC",
        episode_ids
    ).fetchall()

    if len(ep_rows) != len(episode_ids):
        found = {r["id"] for r in ep_rows}
        missing = [e for e in episode_ids if e not in found]
        _log(f"chronicler_batch · missing episodes from DB: {missing}")

    # Build the batch prompt · 1 instruction · 5 episodes · 1 JSON array output
    episode_blocks = []
    for ep in ep_rows:
        events = conn.execute(
            "SELECT id, type, content FROM events WHERE id BETWEEN ? AND ? ORDER BY id ASC",
            (ep["event_start_id"], ep["event_end_id"])
        ).fetchall()
        events_block = _build_event_block(events)
        episode_blocks.append(
            f"--- EPISODE id={ep['id']} ---\n"
            f"episode_name · {ep['episode_name']}\n"
            f"objective · {ep['objective']}\n"
            f"event range · {ep['event_start_id']}-{ep['event_end_id']}\n"
            f"SOURCE EVENTS ·\n{events_block}"
        )
    all_episodes = "\n\n".join(episode_blocks)

    prompt = (
        f"You are {AGENT_CHRONICLER['name']} · the {AGENT_CHRONICLER['role']}. "
        f"Your purpose · {AGENT_CHRONICLER['purpose']}.\n\n"
        "I am giving you MULTIPLE episodes in one shot. For EACH episode, compress it into clean memory. "
        "Preserve every concrete action, every decision, every unresolved thread, every named entity. "
        "Skip the ANSI noise, terminal redraw, spinner output. Reasonable length · 1-2 short paragraphs per episode.\n\n"
        "Output ONLY a JSON ARRAY (no prose, no code fences). Each element MUST have ·\n"
        '{"id": <int>, "summary": str, "actions": [str], "decisions": [str], '
        '"unresolved": [str], "entities": [str]}\n\n'
        f"EPISODES TO SUMMARIZE (count={len(ep_rows)}) ·\n\n"
        f"{all_episodes}\n\n"
        f"Output JSON array · {AGENT_CHRONICLER['name']}:"
    )

    reply = _call_opus_47(prompt, max_tokens=max_tokens_per_call, timeout=timeout)
    if not reply:
        conn.close()
        return {"ok": [], "fail": episode_ids, "reason": "opus_returned_None"}

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        arr = json.loads(reply_clean)
        if not isinstance(arr, list):
            raise ValueError("not a list")
    except Exception as e:
        conn.close()
        _log(f"chronicler_batch · parse fail · {type(e).__name__}: {e} · head={reply[:300]}")
        return {"ok": [], "fail": episode_ids, "reason": f"parse_fail:{type(e).__name__}"}

    # Validate each entry + write valid ones
    written = []
    failed = list(episode_ids)
    now = time.time()
    for entry in arr:
        if not isinstance(entry, dict):
            continue
        eid = entry.get("id")
        if not isinstance(eid, int) or eid not in episode_ids:
            continue
        if "summary" not in entry or not entry["summary"]:
            continue
        # Skip if already summarized (race protection)
        already = conn.execute(
            "SELECT 1 FROM episode_summaries WHERE episode_v2_id = ?", (eid,)
        ).fetchone()
        if already:
            written.append(eid)
            if eid in failed:
                failed.remove(eid)
            continue
        try:
            conn.execute(
                "INSERT INTO episode_summaries (episode_v2_id, summary, actions, decisions, "
                "unresolved, entities, writer_model, written_at) VALUES (?,?,?,?,?,?,?,?)",
                (
                    eid,
                    str(entry.get("summary", ""))[:4000],
                    _arr(entry.get("actions")),
                    _arr(entry.get("decisions")),
                    _arr(entry.get("unresolved")),
                    _arr(entry.get("entities")),
                    batch_writer_model,
                    now,
                )
            )
            written.append(eid)
            if eid in failed:
                failed.remove(eid)
        except Exception as e:
            _log(f"chronicler_batch · insert fail eid={eid} · {type(e).__name__}: {e}")

    conn.commit()
    conn.close()
    return {"ok": written, "fail": failed, "reason": None if not failed else "partial"}


if __name__ == "__main__":
    # Smoke test · summarize 3 most-recent missing episodes
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3, help="batch size for smoke test")
    args = ap.parse_args()

    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    todo = [r[0] for r in conn.execute(
        "SELECT id FROM episodes_v2 "
        "WHERE id NOT IN (SELECT episode_v2_id FROM episode_summaries) "
        "ORDER BY event_end_id DESC LIMIT ?",
        (args.count,)
    ).fetchall()]
    conn.close()

    if not todo:
        print("NOTHING MISSING · L3 complete")
        sys.exit(0)

    print(f"SMOKE · batching {len(todo)} episodes · ids={todo}")
    t0 = time.time()
    result = summarize_batch(todo)
    elapsed = time.time() - t0
    print(f"DONE in {elapsed:.1f}s · {result}")
