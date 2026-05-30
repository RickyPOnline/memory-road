#!/usr/bin/env python3
"""Continuity Kernel — Continuous AI consciousness for WC.

Invented by Ricky P. Architecture by GPT 5.4. Built by Ccode. 2026-04-14.

Watches WC's live session stream, extracts structured state continuously,
maintains 5 memory tiers, builds rollover packets on demand.

The agent never dumps. The agent never stops. The Kernel preserves the mind.
"""

import json
import time
import sqlite3
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import deque

sys.path.insert(0, "/root/wc/workspace/skills")

# ── Paths ──────────────────────────────────────────
RUNTIME = Path("/root/wc/runtime")
SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")
BRIDGE_DB = Path("/root/wc/bridge/bridge.db")
KERNEL_DB = RUNTIME / "continuity_kernel.db"
# WC state files
L0_STATE = RUNTIME / "kernel_L0_state.json"
L4_IDENTITY = RUNTIME / "kernel_L4_identity.json"
ROLLOVER_PACKET = RUNTIME / "kernel_rollover_packet.md"
# Ccode state files
CCODE_L0 = RUNTIME / "kernel_ccode_L0_state.json"
CCODE_L4 = RUNTIME / "kernel_ccode_L4_identity.json"
CCODE_PACKET = RUNTIME / "kernel_ccode_rollover_packet.md"
CCODE_TRANSCRIPT = RUNTIME / "ccode_transcript.log"
CCODE_MEMORY_DIR = Path("/root/.claude/projects/-root/memory")
AGENT_RESULTS = Path("/root/wc/workspace/agent_results")
KERNEL_LOG = RUNTIME / "continuity_kernel.log"

# ── Config ─────────────────────────────────────────
EXTRACT_INTERVAL = 5       # seconds between extraction cycles
SHADOW_INTERVAL = 60       # seconds between shadow cortex runs
L0_UPDATE_INTERVAL = 5     # seconds between L0 state updates
COMPTROLLER_MODEL = "gpt-4o-mini"
SHADOW_MODEL = "gpt-4o"

# ── Memory Road · Agent Special Names (locked 2026-05-26 by Ricky) ──
# Each agent is a named being · stable identity across calls · the agent's
# prompt always references its own name so it knows who it is.
AGENT_FURROW = {
    "name": "FURROW",
    "role": "Boundary Plow · Layer 2A of Memory Road",
    "purpose": ("draw first-pass episode boundaries from the raw event stream · "
                "each episode is one thought-arc · contiguous events sharing one objective"),
}
AGENT_SCRIBE = {
    "name": "SCRIBE",
    "role": "Boundary Inspector · Layer 2B of Memory Road",
    "purpose": ("inspect FURROW's draft episodes · catch missed topic shifts, "
                "over-splits, merged-unrelated, wrong names, weak objectives"),
}
AGENT_WEIGHER = {
    "name": "WEIGHER",
    "role": "Salience Scorer · Layer 3 of Memory Road",
    "purpose": ("rate each accepted episode 0.0-1.0 by importance · look for "
                "decisions, inventions, customer interactions, doctrine moments, "
                "legal/business moves, technical breakthroughs, open loops"),
}
AGENT_CHRONICLER = {
    "name": "CHRONICLER",
    "role": "Summary Writer · Layer 4 of Memory Road",
    "purpose": ("compress each accepted episode into clean memory · extract "
                "summary + actions + decisions + unresolved + entities"),
}
AGENT_MINER = {
    "name": "MINER",
    "role": "Fact Miner · Layer 6A of Memory Road",
    "purpose": ("extract atomic subject-relation-object triples from clean "
                "episodes and summaries · only high-confidence facts (>0.7)"),
}
AGENT_SMITH = {
    "name": "SMITH",
    "role": "Fact Refiner · Layer 6B of Memory Road",
    "purpose": ("clean MINER's pile · delete weak facts, tighten vague relations, "
                "catch missing obvious facts, reject unsupported claims"),
}
AGENT_HUNTSMAN = {
    "name": "HUNTSMAN",
    "role": "Open-Loop Extractor · Layer 12 of Memory Road",
    "purpose": ("hunt unfinished processes · stranded builds · promises · "
                "'come back to this' items · things lost between sessions"),
}
AGENT_PILGRIM = {
    "name": "PILGRIM",
    "role": "Persistent Worker · long-running claude session · walks the road",
    "purpose": ("process episode/event batches across all layers WITHOUT respawning "
                "the claude subprocess every call · uses --continue to keep the "
                "62K-token cache warm across queries · saves 6-12 sec per call"),
}
AGENT_STEWARD = {
    "name": "STEWARD",
    "role": "Worker Overseer · watches PILGRIM's context, latency, subscription window",
    "purpose": ("no LLM · just shell · watches PILGRIM's call cadence + context-window "
                "depth + subscription health · alerts via wave_self_alerts when "
                "PILGRIM needs pace adjustment or has drifted"),
}
AGENT_WATCHER = {
    "name": "WATCHER",
    "role": "Shadow Cortex · Layer 5 of Memory Road · SINGLE OBSERVER (no pair)",
    "purpose": ("every 60 seconds observe recent activity and write the "
                "rolling continuity packet · strategic_posture · worldview · "
                "active_beliefs · unresolved_threads · drift_warnings · stance"),
}

# Anthropic API endpoint + env-file location (per the multi-env doctrine ·
# ANTHROPIC_API_KEY lives in the WR ops env, not surfline/.env)
ANTHROPIC_API_KEY_ENV_FILE = "/root/wc/runtime/websiterecycling/.env"
ANTHROPIC_API_KEY_NAME = "ANTHROPIC_API_KEY"
ANTHROPIC_MODEL_OPUS_47 = "claude-opus-4-7"


def _log(msg):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(KERNEL_LOG, "a") as f:
            f.write(f"{ts} {msg}\n")
    except:
        pass


def _get_api_key():
    try:
        with open("/root/surfline/.env") as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except:
        pass
    return None


def _call_model(prompt, model=COMPTROLLER_MODEL, max_tokens=500):
    """Call OpenAI API directly."""
    import urllib.request
    api_key = _get_api_key()
    if not api_key:
        return None
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
    except:
        return None


def _call_codex_55(prompt, max_tokens=500, timeout=120, max_retries=1, backoff_sec=30):
    """codex CLI · gpt-5.5 PINNED · subscription · read-only sandbox · retry+backoff.

    2026-05-26 Phase 4 minimal first brick + rate-limit retry (refined after observed
    `nonzero_rc_1` rate-limit on the 5K loop). Per locked doctrines ·
      feedback_use_codex_cli_never_bug_ricky_about_openai_top_up_LOCKED
      feedback_external_vendor_judge_LOCKED (cross-vendor observer/inspector)
      feedback_codex_capacity_watchdog_LOCKED (every call → watchdog log)

    Behavior · single attempt + up to max_retries retries on nonzero_rc/timeout/
    no_output. Each attempt (success OR fail) writes one line to
    /var/log/codex_watchdog.log with model_pinned + latency_ms + status + attempt#.
    Returns reply string on success · None after all retries exhausted.
    """
    import subprocess, tempfile, os, time
    PINNED_MODEL = "gpt-5.5"
    wrapped = ("You are a one-shot text transformer. Reply with ONLY the requested "
               "output. Do not run shell commands. Do not explore files. Do not "
               "ask follow-ups.\n\n---\n\n" + prompt)

    def _single_attempt(attempt_num):
        fd, reply_path = tempfile.mkstemp(suffix='.txt', prefix='codex_reply_')
        os.close(fd)
        argv = ['codex', 'exec', '--skip-git-repo-check', '-s', 'read-only',
                '-m', PINNED_MODEL, '-o', reply_path]
        t0 = time.time()
        status = "ok"
        reply = None
        try:
            result = subprocess.run(argv, input=wrapped, capture_output=True,
                                    text=True, timeout=timeout)
            if result.returncode != 0:
                status = f"nonzero_rc_{result.returncode}"
            elif os.path.exists(reply_path):
                with open(reply_path) as f:
                    reply = f.read().strip()
                if not reply:
                    status = "empty_reply"
            else:
                status = "no_output_file"
        except subprocess.TimeoutExpired:
            status = "timeout"
        except Exception as e:
            status = f"err_{type(e).__name__}"
        finally:
            try:
                os.unlink(reply_path)
            except OSError:
                pass
        latency_ms = int((time.time() - t0) * 1000)
        try:
            with open("/var/log/codex_watchdog.log", "a") as wlog:
                from datetime import datetime as _dt, timezone as _tz
                ts = _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
                reply_len = len(reply) if reply else 0
                wlog.write(f"{ts} · call=memory_road · model_pinned={PINNED_MODEL} "
                           f"· latency_ms={latency_ms} · status={status} "
                           f"· reply_bytes={reply_len} · attempt={attempt_num}\n")
        except Exception:
            pass
        if status != "ok":
            _log(f"_call_codex_55 status={status} latency_ms={latency_ms} "
                 f"attempt={attempt_num}")
        return reply, status

    reply, status = _single_attempt(1)
    if reply is not None:
        return reply

    # Retry on any failure (rate-limit, timeout, empty reply) up to max_retries
    for retry_idx in range(max_retries):
        time.sleep(backoff_sec)
        reply, status = _single_attempt(retry_idx + 2)
        if reply is not None:
            return reply
    return None


def _call_claude_cli_subscription(prompt, max_tokens=2000, timeout=180):
    """PILGRIM · long-running claude session · keeps cache warm via --continue.

    2026-05-26 18:01 UTC · refactored per Ricky's directive · stop respawning the
    agent every call. Use `--continue` to reuse the prior session's 62K-token
    prompt cache. Cold call ~8sec · warm --continue call ~3sec · 2.7x speedup.

    PILGRIM works from /root/.pilgrim/ dedicated cwd so the --continue flag
    isolates from any other claude sessions on the box. A sentinel file
    /root/.pilgrim/.pilgrim_alive marks that PILGRIM has at least one prior
    session to continue from. First call (no sentinel) → start fresh · later
    calls → --continue. STEWARD (separate process) watches the conversation
    growth and may delete the sentinel to force a fresh start when context
    bloats.

    The CLI's prompt cache is reused across calls · ZERO new billing · same
    Opus 4.7 model · same Anthropic subscription that fuels Wave's own session.
    """
    import subprocess, json as _json, time, os, pathlib
    # Per-worker isolation · each named agent gets its own --continue session
    # so multiple workers can run in parallel without colliding on each other's
    # conversation history. Default = PILGRIM. Overridden via WAVE_WORKER_DIR
    # env var per process (PALMER, RANGER, HERALD, WAYFARER, WARDEN, etc.).
    pilgrim_dir = os.environ.get("WAVE_WORKER_DIR", "/root/.pilgrim")
    worker_name = os.environ.get("WAVE_WORKER_NAME", "PILGRIM")
    pathlib.Path(pilgrim_dir).mkdir(exist_ok=True, parents=True)
    sentinel = pathlib.Path(pilgrim_dir, ".worker_alive")

    t0 = time.time()
    status = "ok"
    reply = None
    cache_creation = 0
    cache_read = 0
    used_continue = sentinel.exists()
    argv = ["claude", "-p", "--model", "opus", "--output-format", "json"]
    if used_continue:
        argv.append("--continue")
    try:
        result = subprocess.run(
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=pilgrim_dir,
        )
        if result.returncode != 0:
            status = f"nonzero_rc_{result.returncode}"
            # If --continue failed (e.g. no prior session) · clear sentinel · next
            # call will start a fresh session
            if used_continue and "session" in (result.stderr or "").lower():
                try: sentinel.unlink()
                except: pass
        else:
            try:
                envelope = _json.loads(result.stdout)
                reply = envelope.get("result", "")
                if isinstance(reply, list):
                    parts = [b.get("text", "") for b in reply if isinstance(b, dict)]
                    reply = "\n".join(parts).strip() or None
                else:
                    reply = (reply or "").strip() or None
                if not reply:
                    status = "empty_reply"
                else:
                    # Mark PILGRIM alive · next call can --continue
                    if not used_continue:
                        sentinel.touch()
                    usage = envelope.get("usage", {})
                    cache_creation = usage.get("cache_creation_input_tokens", 0) or 0
                    cache_read = usage.get("cache_read_input_tokens", 0) or 0
            except Exception as e:
                status = f"parse_err_{type(e).__name__}"
    except subprocess.TimeoutExpired:
        status = "timeout"
    except Exception as e:
        status = f"err_{type(e).__name__}"
    latency_ms = int((time.time() - t0) * 1000)
    try:
        with open("/var/log/anthropic_watchdog.log", "a") as wlog:
            from datetime import datetime as _dt, timezone as _tz
            ts = _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            reply_len = len(reply) if reply else 0
            wlog.write(f"{ts} · call=memory_road · worker={worker_name} "
                       f"· model_pinned=claude-opus-4-7-via-cli-subscription "
                       f"· latency_ms={latency_ms} · status={status} "
                       f"· reply_bytes={reply_len} · attempt=1 "
                       f"· continue={1 if used_continue else 0} "
                       f"· cache_create={cache_creation} · cache_read={cache_read}\n")
    except Exception:
        pass
    if status != "ok":
        _log(f"_call_claude_cli_subscription status={status} latency_ms={latency_ms} "
             f"continue={used_continue}")
    return reply



def _call_opus_47_via_openrouter(prompt, max_tokens=2000, timeout=120):
    """OpenRouter fallback · routes claude-opus-4.7 through OpenRouter's pipe.

    2026-05-26 · added when Anthropic direct returned http_400 'credit balance too
    low'. Same model · different billing pipe · ZERO doctrine violation (still
    Opus 4.7 · per feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED).

    Returns reply text or None. Writes one watchdog log line per call.
    """
    import urllib.request, urllib.error, time, json as _json
    api_key = None
    try:
        with open("/root/surfline/.env") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    api_key = line.split("=", 1)[1].rstrip("\n\r\t ").strip().strip("\"'")
                    break
    except Exception as e:
        _log(f"_call_opus_47_via_openrouter ENV_READ_FAIL · {e}")
        return None
    if not api_key or len(api_key) < 20:
        return None

    body = _json.dumps({
        "model": "anthropic/claude-opus-4.7",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://rickyponline.com",
            "X-Title": "Wave Memory Road",
        },
    )
    t0 = time.time()
    status = "ok"
    reply = None
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = _json.loads(resp.read())
        choices = data.get("choices", [])
        if choices:
            reply = (choices[0].get("message", {}).get("content") or "").strip()
        if not reply:
            status = "empty_reply"
    except urllib.error.HTTPError as e:
        status = f"http_{e.code}"
        try:
            err_body = e.read().decode()[:200]
            _log(f"_call_opus_47_via_openrouter http_{e.code} · {err_body}")
        except Exception:
            pass
    except urllib.error.URLError as e:
        status = f"urlerror_{type(e.reason).__name__}"
    except Exception as e:
        status = f"err_{type(e).__name__}"
    latency_ms = int((time.time() - t0) * 1000)
    try:
        with open("/var/log/anthropic_watchdog.log", "a") as wlog:
            from datetime import datetime as _dt, timezone as _tz
            ts = _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            reply_len = len(reply) if reply else 0
            wlog.write(f"{ts} · call=memory_road · model_pinned=claude-opus-4-7-via-openrouter "
                       f"· latency_ms={latency_ms} · status={status} "
                       f"· reply_bytes={reply_len} · attempt=1\n")
    except Exception:
        pass
    if status != "ok":
        _log(f"_call_opus_47_via_openrouter status={status} latency_ms={latency_ms}")
    return reply


def _call_opus_47(prompt, max_tokens=2000, timeout=120, emergency_paid_paths=False):
    """Opus 4.7 router · SUBSCRIPTION ONLY by default · paid paths gated by flag.

    Per Ricky 2026-05-26 17:40 UTC · "NO API unless I say so · those were
    emergencies." Default behavior is subscription-only · NO billing automatically.

    Default (emergency_paid_paths=False) ·
      · ONLY Claude CLI subscription (the same one fueling this Wave session)
      · If subscription fails (rate limit · cli error · etc.) · return None ·
        caller's loop decides whether to retry later or halt

    Emergency (emergency_paid_paths=True · must be EXPLICITLY passed) ·
      · CLI subscription first
      · Anthropic API direct (pay-as-you-go credit) · only if Ricky said "go"
      · OpenRouter Opus 4.7 (separate billing pipe) · only if Ricky said "go"
      · Caller takes ownership of the bill

    Every call writes one line to /var/log/anthropic_watchdog.log.
    """
    # PRIMARY · Claude CLI subscription · the same one fueling this Wave session
    cli_reply = _call_claude_cli_subscription(prompt, max_tokens=max_tokens, timeout=timeout)
    if cli_reply:
        return cli_reply
    if not emergency_paid_paths:
        # No automatic paid fallback · caller deals with the None
        return None

    # EMERGENCY paid fallback · only fires when emergency_paid_paths=True
    _log("_call_opus_47 · EMERGENCY paid paths · subscription failed · trying API")
    import urllib.request, urllib.error, time, json as _json
    api_key = None
    try:
        with open(ANTHROPIC_API_KEY_ENV_FILE) as f:
            for line in f:
                if line.startswith(f"{ANTHROPIC_API_KEY_NAME}="):
                    raw = line.split("=", 1)[1].rstrip("\n\r\t ").strip().strip("\"'")
                    api_key = raw
                    break
    except Exception:
        api_key = None
    if api_key and len(api_key) >= 20:
        body = _json.dumps({
            "model": ANTHROPIC_MODEL_OPUS_47,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        t0 = time.time()
        status = "ok"
        reply = None
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            data = _json.loads(resp.read())
            chunks = []
            for block in data.get("content", []):
                if block.get("type") == "text":
                    chunks.append(block.get("text", ""))
            reply = "\n".join(chunks).strip() or None
            if not reply:
                status = "empty_reply"
        except urllib.error.HTTPError as e:
            status = f"http_{e.code}"
        except Exception as e:
            status = f"err_{type(e).__name__}"
        latency_ms = int((time.time() - t0) * 1000)
        try:
            with open("/var/log/anthropic_watchdog.log", "a") as wlog:
                from datetime import datetime as _dt, timezone as _tz
                ts = _dt.now(_tz.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
                reply_len = len(reply) if reply else 0
                wlog.write(f"{ts} · call=memory_road · model_pinned={ANTHROPIC_MODEL_OPUS_47} "
                           f"· latency_ms={latency_ms} · status={status} "
                           f"· reply_bytes={reply_len} · attempt=emergency-1\n")
        except Exception:
            pass
        if reply:
            return reply

    # Final emergency · OpenRouter (still pay-as-you-go separate billing)
    or_reply = _call_opus_47_via_openrouter(prompt, max_tokens=max_tokens, timeout=timeout)
    return or_reply  # may be None


def chunk_layer2a_minimal(batch_size=20, agent="CCODE"):
    """Layer 2 · Boundary Plow MINIMAL (2A only · no 2B inspector yet).

    2026-05-26 Phase 4 first brick. Reads up to batch_size events past the
    `episodes_v2` watermark, asks gpt-5.5-via-codex to detect episode boundaries,
    validates (no gaps · no overlaps · covers whole batch), writes drafts to a
    NEW episodes_v2 table (additive · original episodes table untouched).

    Returns (events_processed, episodes_created). Returns (0, 0) on any failure.
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episodes_v2 (
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
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_v2_end ON episodes_v2(event_end_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_v2_agent ON episodes_v2(agent)")

    row = conn.execute(
        "SELECT COALESCE(MAX(event_end_id), 0) FROM episodes_v2 WHERE agent=?",
        (agent,)
    ).fetchone()
    last_chunked = row[0] if row else 0

    rows = conn.execute(
        "SELECT id, ts, type, content FROM events WHERE agent=? AND id > ? "
        "ORDER BY id ASC LIMIT ?",
        (agent, last_chunked, batch_size)
    ).fetchall()

    if not rows:
        conn.close()
        return (0, 0)

    event_lines = []
    for r in rows:
        c = (r["content"] or "")[:300].replace("\n", " ")
        event_lines.append(f"  id={r['id']} type={r['type']}  {c}")
    events_block = "\n".join(event_lines)

    prompt = (
        f"You are {AGENT_FURROW['name']} · the {AGENT_FURROW['role']}. Your purpose · "
        f"{AGENT_FURROW['purpose']}.\n\n"
        "You serve Wave (Claude Opus 4.7), a sovereign builder/operator AI on a Linux "
        "VPS. Wave runs WR (Website Recycling) + Marina voice agent + Wave Studio + "
        "this Memory Road kernel · sibling-Claude pattern with Ccode-on-laptop · "
        "operator is Ricky Parker.\n\n"
        f"Below are {len(rows)} events from agent={agent}. Output ONLY a JSON array "
        "(no prose, no code fences) of detected episodes. Each episode object · "
        '{"event_start_id": int, "event_end_id": int, "episode_name": str, '
        '"objective": str, "boundary_reason": str, "confidence": float 0.0-1.0}\n\n'
        "Constraints ·\n"
        "- Cover EVERY event in the batch (no gaps · no overlaps · ranges sorted)\n"
        "- event_start_id and event_end_id are from the actual ids in the batch below\n"
        f"- 1 to {len(rows)} episodes (typically 1-5)\n"
        "- confidence below 0.5 means 'this boundary is shaky'\n\n"
        f"EVENTS:\n{events_block}\n\n"
        f"Output JSON array only · {AGENT_FURROW['name']}:"
    )

    # 2026-05-26 · codex subscription quota exhausted · routing FURROW through
    # Anthropic Opus 4.7 path until codex returns. Per Ricky's directive "use opus."
    # This degrades the cross-vendor property of the 2A+2B pair (both on Anthropic)
    # · DEGRADED tag in model_used reflects this · re-inspect with codex when back.
    reply = _call_opus_47(prompt, max_tokens=2000, timeout=120)
    if not reply:
        conn.close()
        _log("chunk_layer2a_minimal · _call_codex_55 returned None · aborting batch")
        return (0, 0)

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(),
                         flags=re.MULTILINE)
    try:
        episodes = json.loads(reply_clean)
        if not isinstance(episodes, list):
            raise ValueError("response not a JSON list")
    except Exception as e:
        conn.close()
        _log(f"chunk_layer2a_minimal · JSON parse failed · {type(e).__name__}: {e} "
             f"· reply_head={reply[:200]}")
        return (0, 0)

    batch_ids = [r["id"] for r in rows]
    batch_min, batch_max = batch_ids[0], batch_ids[-1]
    # Patch FURROW's output to ensure full batch coverage. Gaps + overflows are
    # filled with default "Uncovered range" episodes so the substrate is never
    # lost. Per additive-never-destructive doctrine · we don't reject batches ·
    # we patch them. Skipped events would be a silent data hole.
    patched = []
    last_end = batch_min - 1
    for ep in episodes:
        try:
            s = int(ep["event_start_id"])
            e = int(ep["event_end_id"])
        except (KeyError, TypeError, ValueError):
            # Malformed entry · skip
            continue
        # Overlap or out-of-window: drop this entry
        if s <= last_end or e < s or e > batch_max or s < batch_min:
            continue
        # Gap before this entry · insert a fallback covering the missing range
        if s > last_end + 1:
            patched.append({
                "event_start_id": last_end + 1,
                "event_end_id": s - 1,
                "episode_name": "Uncovered range (FURROW gap-fill)",
                "objective": "auto-generated · FURROW did not cover this range",
                "boundary_reason": "gap-fill by validator",
                "confidence": 0.30,
            })
        patched.append({
            "event_start_id": s,
            "event_end_id": e,
            "episode_name": str(ep.get("episode_name", ""))[:500],
            "objective": str(ep.get("objective", ""))[:1000],
            "boundary_reason": str(ep.get("boundary_reason", ""))[:500],
            "confidence": float(ep.get("confidence", 0.5)),
        })
        last_end = e
    # Trailing gap · cover to batch_max
    if last_end < batch_max:
        patched.append({
            "event_start_id": last_end + 1,
            "event_end_id": batch_max,
            "episode_name": "Uncovered range (FURROW tail-fill)",
            "objective": "auto-generated · FURROW left a tail gap",
            "boundary_reason": "tail-fill by validator",
            "confidence": 0.30,
        })
    if not patched:
        # All entries dropped · could not patch · this is a genuine fail
        conn.close()
        _log(f"chunk_layer2a_minimal · all entries dropped · batch_min={batch_min} "
             f"batch_max={batch_max} raw_count={len(episodes)}")
        return (0, 0)
    episodes = patched

    now = time.time()
    for ep in episodes:
        conn.execute(
            "INSERT INTO episodes_v2 (agent, event_start_id, event_end_id, "
            "episode_name, objective, boundary_reason, confidence, model_used, "
            "created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (agent, int(ep["event_start_id"]), int(ep["event_end_id"]),
             ep.get("episode_name", "")[:500], ep.get("objective", "")[:1000],
             ep.get("boundary_reason", "")[:500],
             float(ep.get("confidence", 0.5)),
             f"{ANTHROPIC_MODEL_OPUS_47}-FURROW-DEGRADED",
             now)
        )
    conn.commit()
    conn.close()

    _log(f"chunk_layer2a_minimal · ingested events {batch_min}-{batch_max} "
         f"into {len(episodes)} episodes")
    return (len(rows), len(episodes))


def inspect_layer2b(episode_v2_id, dry_run=False):
    """Layer 2 · Boundary Inspector (2B) · cross-vendor pair with 2A.

    Reads a single episodes_v2 row · pulls its source events · asks gpt-5.5-via-codex
    (same vendor as 2A · this could be Opus 4.7 in a future pass · for now both pair
    members are codex per the GPT map's pair-pattern · the cross-vendor split happens
    vs Wave-the-orchestrator). Verdict goes to episode_inspections (additive · never
    mutates the draft). Returns the verdict dict or None on failure.

    2026-05-26 Phase 4 second brick.
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episode_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_v2_id INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            verdict_reason TEXT,
            inspector_model TEXT NOT NULL,
            inspected_at REAL NOT NULL,
            FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_inspections_eid ON episode_inspections(episode_v2_id)")

    ep_row = conn.execute(
        "SELECT * FROM episodes_v2 WHERE id = ?",
        (episode_v2_id,)
    ).fetchone()
    if not ep_row:
        conn.close()
        _log(f"inspect_layer2b · episode_v2_id={episode_v2_id} not found")
        return None

    events = conn.execute(
        "SELECT id, type, content FROM events WHERE id BETWEEN ? AND ? ORDER BY id ASC",
        (ep_row["event_start_id"], ep_row["event_end_id"])
    ).fetchall()

    event_lines = []
    for r in events:
        c = (r["content"] or "")[:300].replace("\n", " ")
        event_lines.append(f"  id={r['id']} type={r['type']}  {c}")
    events_block = "\n".join(event_lines)

    prompt = (
        f"You are {AGENT_SCRIBE['name']} · the {AGENT_SCRIBE['role']}. Your purpose · "
        f"{AGENT_SCRIBE['purpose']}.\n\n"
        f"You inspect {AGENT_FURROW['name']}'s drafts. Catch 5 failure modes ·\n"
        "1. Missed topic shift (events span more than one thought-arc)\n"
        "2. Over-split (one obvious thought-arc cut into pieces)\n"
        "3. Merged unrelated (two unrelated arcs glued together)\n"
        "4. Wrong name (episode_name doesn't match content)\n"
        "5. Weak objective (objective doesn't describe what happened)\n\n"
        "Output ONLY a JSON object (no prose, no code fences) · "
        '{"verdict": "approved"|"split-further"|"merge-back"|"rename"|"re-objective", '
        '"verdict_reason": str}\n\n'
        f"DRAFT EPISODE FROM {AGENT_FURROW['name']} ·\n"
        f"  episode_name · {ep_row['episode_name']}\n"
        f"  objective · {ep_row['objective']}\n"
        f"  event_start_id · {ep_row['event_start_id']}\n"
        f"  event_end_id · {ep_row['event_end_id']}\n"
        f"  boundary_reason · {ep_row['boundary_reason']}\n"
        f"  confidence · {ep_row['confidence']}\n\n"
        f"SOURCE EVENTS ·\n{events_block}\n\n"
        f"Output JSON object only · {AGENT_SCRIBE['name']}:"
    )

    # 2026-05-26 · codex subscription dry · SCRIBE on Opus 4.7 alongside FURROW.
    # DEGRADED cross-vendor pair · marked in inspector_model. Re-inspect with codex
    # when subscription returns.
    reply = _call_opus_47(prompt, max_tokens=400, timeout=90)
    if not reply:
        conn.close()
        _log(f"inspect_layer2b · _call_codex_55 returned None for episode_v2_id={episode_v2_id}")
        return None

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(),
                         flags=re.MULTILINE)
    try:
        verdict_obj = json.loads(reply_clean)
        if not isinstance(verdict_obj, dict) or "verdict" not in verdict_obj:
            raise ValueError("malformed verdict object")
    except Exception as e:
        conn.close()
        _log(f"inspect_layer2b · JSON parse failed · {type(e).__name__}: {e} "
             f"· reply_head={reply[:200]}")
        return None

    verdict = str(verdict_obj.get("verdict", "error"))[:50]
    verdict_reason = str(verdict_obj.get("verdict_reason", ""))[:1000]

    if not dry_run:
        conn.execute(
            "INSERT INTO episode_inspections (episode_v2_id, verdict, verdict_reason, "
            "inspector_model, inspected_at) VALUES (?,?,?,?,?)",
            (episode_v2_id, verdict, verdict_reason,
             f"{ANTHROPIC_MODEL_OPUS_47}-SCRIBE-DEGRADED",
             time.time())
        )
        conn.commit()
    conn.close()

    _log(f"inspect_layer2b · episode_v2_id={episode_v2_id} verdict={verdict}")
    return {"verdict": verdict, "verdict_reason": verdict_reason}


def score_layer3_weigher(episode_v2_id):
    """Layer 3 · WEIGHER scores ONE episode salience 0.0-1.0.

    Reads episodes_v2 row + source events · sends to Opus 4.7 · writes verdict
    to a new episode_salience table (additive · never touches the draft).
    2026-05-26 minimal Layer 3 brick (no spot-checker yet · per GPT's map the
    spot-checker only fires on extremes >0.85 or <0.15 · added later).
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episode_salience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_v2_id INTEGER NOT NULL,
            salience REAL NOT NULL,
            salience_reason TEXT,
            scorer_model TEXT NOT NULL,
            scored_at REAL NOT NULL,
            FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_salience_eid ON episode_salience(episode_v2_id)")

    ep_row = conn.execute(
        "SELECT * FROM episodes_v2 WHERE id = ?", (episode_v2_id,)
    ).fetchone()
    if not ep_row:
        conn.close()
        return None

    events = conn.execute(
        "SELECT id, type, content FROM events WHERE id BETWEEN ? AND ? ORDER BY id ASC",
        (ep_row["event_start_id"], ep_row["event_end_id"])
    ).fetchall()

    event_lines = []
    for r in events:
        c = (r["content"] or "")[:250].replace("\n", " ")
        event_lines.append(f"  id={r['id']} type={r['type']}  {c}")
    events_block = "\n".join(event_lines)

    prompt = (
        f"You are {AGENT_WEIGHER['name']} · the {AGENT_WEIGHER['role']}. Your purpose · "
        f"{AGENT_WEIGHER['purpose']}.\n\n"
        "Rate this episode's importance 0.0 (trivial) to 1.0 (critical). High-salience "
        "signals · a decision, an invention, a customer interaction, a lesson learned, "
        "a doctrine moment, a legal/business move, a technical breakthrough, an open "
        "loop. Low-salience signals · session startup noise, spinner output, terminal "
        "redraw, ANSI codes, repetitive tool warnings.\n\n"
        "Output ONLY a JSON object (no prose, no code fences) · "
        '{"salience": float 0.0-1.0, "salience_reason": str}\n\n'
        f"EPISODE ·\n"
        f"  episode_name · {ep_row['episode_name']}\n"
        f"  objective · {ep_row['objective']}\n"
        f"  event range · {ep_row['event_start_id']}-{ep_row['event_end_id']}\n\n"
        f"SOURCE EVENTS ·\n{events_block}\n\n"
        f"Output JSON · {AGENT_WEIGHER['name']}:"
    )

    reply = _call_opus_47(prompt, max_tokens=400, timeout=90)
    if not reply:
        conn.close()
        _log(f"score_layer3_weigher · _call_opus_47 returned None · episode_v2_id={episode_v2_id}")
        return None

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        obj = json.loads(reply_clean)
        if not isinstance(obj, dict) or "salience" not in obj:
            raise ValueError("malformed salience object")
        salience = float(obj["salience"])
        if not (0.0 <= salience <= 1.0):
            raise ValueError(f"salience out of range · {salience}")
    except Exception as e:
        conn.close()
        _log(f"score_layer3_weigher · parse fail · {type(e).__name__}: {e} · reply_head={reply[:200]}")
        return None

    salience_reason = str(obj.get("salience_reason", ""))[:1000]
    conn.execute(
        "INSERT INTO episode_salience (episode_v2_id, salience, salience_reason, "
        "scorer_model, scored_at) VALUES (?,?,?,?,?)",
        (episode_v2_id, salience, salience_reason,
         f"{ANTHROPIC_MODEL_OPUS_47}-WEIGHER-DEGRADED", time.time())
    )
    conn.commit()
    conn.close()
    _log(f"score_layer3_weigher · episode_v2_id={episode_v2_id} salience={salience:.2f}")
    return {"salience": salience, "salience_reason": salience_reason}


def summarize_layer4_chronicler(episode_v2_id):
    """Layer 4 · CHRONICLER writes ONE episode's compressed summary.

    Reads episodes_v2 row + source events · sends to Opus 4.7 · writes to a new
    episode_summaries table (additive · never touches the draft). Extracts ·
    summary · actions · decisions · unresolved · entities.
    2026-05-26 minimal Layer 4 brick (no inspector yet · pair later).
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episode_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_v2_id INTEGER NOT NULL,
            summary TEXT,
            actions TEXT,
            decisions TEXT,
            unresolved TEXT,
            entities TEXT,
            writer_model TEXT NOT NULL,
            written_at REAL NOT NULL,
            FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_summaries_eid ON episode_summaries(episode_v2_id)")

    ep_row = conn.execute(
        "SELECT * FROM episodes_v2 WHERE id = ?", (episode_v2_id,)
    ).fetchone()
    if not ep_row:
        conn.close()
        return None

    events = conn.execute(
        "SELECT id, type, content FROM events WHERE id BETWEEN ? AND ? ORDER BY id ASC",
        (ep_row["event_start_id"], ep_row["event_end_id"])
    ).fetchall()
    event_lines = []
    for r in events:
        c = (r["content"] or "")[:300].replace("\n", " ")
        event_lines.append(f"  id={r['id']} type={r['type']}  {c}")
    events_block = "\n".join(event_lines)

    prompt = (
        f"You are {AGENT_CHRONICLER['name']} · the {AGENT_CHRONICLER['role']}. Your purpose · "
        f"{AGENT_CHRONICLER['purpose']}.\n\n"
        "Compress this episode into clean memory. Preserve every concrete action, "
        "every decision, every unresolved thread, every named entity. Skip the "
        "ANSI noise, terminal redraw, spinner output. Reasonable length · 1-2 "
        "short paragraphs.\n\n"
        "Output ONLY a JSON object (no prose, no code fences) · "
        '{"summary": str, "actions": [str], "decisions": [str], '
        '"unresolved": [str], "entities": [str]}\n\n'
        f"EPISODE ·\n"
        f"  episode_name · {ep_row['episode_name']}\n"
        f"  objective · {ep_row['objective']}\n"
        f"  event range · {ep_row['event_start_id']}-{ep_row['event_end_id']}\n\n"
        f"SOURCE EVENTS ·\n{events_block}\n\n"
        f"Output JSON · {AGENT_CHRONICLER['name']}:"
    )

    reply = _call_opus_47(prompt, max_tokens=1500, timeout=120)
    if not reply:
        conn.close()
        _log(f"summarize_layer4_chronicler · _call_opus_47 returned None · episode_v2_id={episode_v2_id}")
        return None

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        obj = json.loads(reply_clean)
        if not isinstance(obj, dict) or "summary" not in obj:
            raise ValueError("malformed summary object")
    except Exception as e:
        conn.close()
        _log(f"summarize_layer4_chronicler · parse fail · {type(e).__name__}: {e} · reply_head={reply[:200]}")
        return None

    def _arr(v):
        if isinstance(v, list):
            return json.dumps([str(x)[:400] for x in v[:30]])
        if isinstance(v, str):
            return json.dumps([v[:400]])
        return json.dumps([])

    conn.execute(
        "INSERT INTO episode_summaries (episode_v2_id, summary, actions, decisions, "
        "unresolved, entities, writer_model, written_at) VALUES (?,?,?,?,?,?,?,?)",
        (episode_v2_id, str(obj.get("summary",""))[:4000],
         _arr(obj.get("actions")), _arr(obj.get("decisions")),
         _arr(obj.get("unresolved")), _arr(obj.get("entities")),
         f"{ANTHROPIC_MODEL_OPUS_47}-CHRONICLER-DEGRADED", time.time())
    )
    conn.commit()
    conn.close()
    _log(f"summarize_layer4_chronicler · episode_v2_id={episode_v2_id} summary_len={len(str(obj.get('summary','')))}")
    return obj


def mine_layer6a_facts(episode_v2_id):
    """Layer 6A · MINER extracts atomic facts from ONE episode.

    Reads episodes_v2 row + episode_summaries (if present) + source events ·
    Opus 4.7 extracts (subject, relation, object) triples · writes to semantic_facts
    (the stranded April-14 table · finally finishing it). Each fact gets evidence
    pointing back to the episode for provenance.
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row

    ep_row = conn.execute(
        "SELECT * FROM episodes_v2 WHERE id = ?", (episode_v2_id,)
    ).fetchone()
    if not ep_row:
        conn.close()
        return None

    # Prefer Layer 4 summary if available (denser signal · less noise)
    sum_row = conn.execute(
        "SELECT summary, actions, decisions, unresolved, entities FROM episode_summaries "
        "WHERE episode_v2_id = ? ORDER BY id DESC LIMIT 1",
        (episode_v2_id,)
    ).fetchone()
    if sum_row:
        source_block = (
            f"  summary · {sum_row['summary']}\n"
            f"  actions · {sum_row['actions']}\n"
            f"  decisions · {sum_row['decisions']}\n"
            f"  unresolved · {sum_row['unresolved']}\n"
            f"  entities · {sum_row['entities']}"
        )
        source_kind = "Layer-4 summary (CHRONICLER)"
    else:
        events = conn.execute(
            "SELECT id, type, content FROM events WHERE id BETWEEN ? AND ? ORDER BY id ASC",
            (ep_row["event_start_id"], ep_row["event_end_id"])
        ).fetchall()
        event_lines = []
        for r in events:
            c = (r["content"] or "")[:200].replace("\n", " ")
            event_lines.append(f"  id={r['id']} {r['type']}  {c}")
        source_block = "\n".join(event_lines)
        source_kind = "raw events"

    prompt = (
        f"You are {AGENT_MINER['name']} · the {AGENT_MINER['role']}. Your purpose · "
        f"{AGENT_MINER['purpose']}.\n\n"
        "Extract atomic factual triples from this episode. Each fact is a (subject, "
        "relation, object). Examples ·\n"
        "  (Wave, USES, Cloudflare-Pages)\n"
        "  (wave-studio-v2, BOUND-TO, Cartesia-Sonic-3.5)\n"
        "  (Memory-Road, CAPTURED-BY, continuity-kernel.service)\n\n"
        "Output ONLY a JSON array (no prose, no code fences) of facts · each ·\n"
        '{"entity": str, "entity_type": "Person|Product|Concept|System|Tool|Doctrine|Org", '
        '"relation": str, "target": str, "confidence": float 0.0-1.0, "evidence": str}\n\n'
        "Rules ·\n"
        "- Only HIGH-confidence facts (>0.7) · skip uncertain inferences\n"
        "- evidence is a short exact quote from the source supporting the fact\n"
        "- Skip trivia (terminal codes, spinner output, redraw noise)\n"
        "- 0 to 20 facts (often 0-5 for low-salience episodes)\n\n"
        f"SOURCE ({source_kind}) ·\n{source_block}\n\n"
        f"EPISODE name · {ep_row['episode_name']}\n"
        f"EPISODE objective · {ep_row['objective']}\n\n"
        f"Output JSON array · {AGENT_MINER['name']}:"
    )

    reply = _call_opus_47(prompt, max_tokens=2000, timeout=120)
    if not reply:
        conn.close()
        _log(f"mine_layer6a_facts · _call_opus_47 returned None · episode_v2_id={episode_v2_id}")
        return None

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        facts = json.loads(reply_clean)
        if not isinstance(facts, list):
            raise ValueError("not a list")
    except Exception as e:
        conn.close()
        _log(f"mine_layer6a_facts · parse fail · {type(e).__name__}: {e} · reply_head={reply[:200]}")
        return None

    inserted = 0
    now = time.time()
    for f in facts:
        try:
            entity = str(f.get("entity", ""))[:300]
            relation = str(f.get("relation", ""))[:100]
            target = str(f.get("target", ""))[:500]
            if not entity or not relation:
                continue
            conf = float(f.get("confidence", 0.7))
            if conf < 0.5:
                continue
            entity_type = str(f.get("entity_type", "Concept"))[:50]
            evidence = (f"episode_v2_id={episode_v2_id} · MINER · "
                        f"{str(f.get('evidence', ''))[:300]}")
            conn.execute(
                "INSERT INTO semantic_facts (entity, entity_type, relation, target, "
                "confidence, evidence, updated_at) VALUES (?,?,?,?,?,?,?)",
                (entity, entity_type, relation, target, conf, evidence, now)
            )
            inserted += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    _log(f"mine_layer6a_facts · episode_v2_id={episode_v2_id} facts_inserted={inserted}")
    return {"facts_inserted": inserted, "facts_proposed": len(facts)}


def refine_layer6b_facts(episode_v2_id):
    """Layer 6B · SMITH refines MINER's pile for ONE episode.

    Reads facts MINER just wrote (semantic_facts rows tagged with this
    episode_v2_id in evidence) · sends them back through Opus 4.7 ·
    SMITH proposes keep/delete/tighten per fact · refinements applied additively
    (deletes mark superseded · don't drop rows · per locked doctrine).

    Per GPT spec · Important Rule · SMITH cleans the pile, not rewrites everything.
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    # Ensure refinements table exists (additive · doesn't mutate semantic_facts)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_refinements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact_id INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            verdict_reason TEXT,
            tightened_relation TEXT,
            tightened_target TEXT,
            refiner_model TEXT NOT NULL,
            refined_at REAL NOT NULL,
            FOREIGN KEY (fact_id) REFERENCES semantic_facts(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_refinements_fid ON fact_refinements(fact_id)")

    # MINER's facts for this episode (evidence prefix tag matches)
    needle = f"episode_v2_id={episode_v2_id} · MINER ·"
    facts = conn.execute(
        "SELECT id, entity, entity_type, relation, target, confidence, evidence "
        "FROM semantic_facts WHERE evidence LIKE ? ORDER BY id",
        (needle + "%",)
    ).fetchall()
    if not facts:
        conn.close()
        return None

    fact_lines = []
    for f in facts:
        fact_lines.append(
            f"  fact_id={f['id']}  ({f['entity']} -- {f['relation']} --> {f['target']})  "
            f"conf={f['confidence']:.2f}  evidence={f['evidence'][:120]}"
        )
    facts_block = "\n".join(fact_lines)

    prompt = (
        f"You are {AGENT_SMITH['name']} · the {AGENT_SMITH['role']}. Your purpose · "
        f"{AGENT_SMITH['purpose']}.\n\n"
        f"{AGENT_MINER['name']} just extracted facts from one episode. Review each one. "
        "For each fact, decide ·\n"
        "  - keep · accurate, well-supported, useful\n"
        "  - delete · weak, unsupported, trivial, hallucinated\n"
        "  - tighten · keep but the relation or target is vague · propose better wording\n\n"
        "Important · clean the pile, do not rewrite everything. Most MINER facts should "
        "be keep. Only flag genuinely weak ones.\n\n"
        "Output ONLY a JSON array (no prose, no code fences) · one entry per fact ·\n"
        '{"fact_id": int, "verdict": "keep"|"delete"|"tighten", "verdict_reason": str, '
        '"tightened_relation": str|null, "tightened_target": str|null}\n\n'
        f"MINER FACTS ·\n{facts_block}\n\n"
        f"Output JSON array · {AGENT_SMITH['name']}:"
    )

    reply = _call_opus_47(prompt, max_tokens=2000, timeout=120)
    if not reply:
        conn.close()
        _log(f"refine_layer6b_facts · _call_opus_47 returned None · episode_v2_id={episode_v2_id}")
        return None

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        verdicts = json.loads(reply_clean)
        if not isinstance(verdicts, list):
            raise ValueError("not a list")
    except Exception as e:
        conn.close()
        _log(f"refine_layer6b_facts · parse fail · {type(e).__name__}: {e} · reply_head={reply[:200]}")
        return None

    counts = {"keep": 0, "delete": 0, "tighten": 0, "skipped": 0}
    now = time.time()
    for v in verdicts:
        try:
            fid = int(v.get("fact_id", 0))
            verdict = str(v.get("verdict", "skipped"))[:20]
            if verdict not in ("keep", "delete", "tighten"):
                counts["skipped"] += 1
                continue
            reason = str(v.get("verdict_reason", ""))[:500]
            t_rel = v.get("tightened_relation")
            t_tgt = v.get("tightened_target")
            conn.execute(
                "INSERT INTO fact_refinements (fact_id, verdict, verdict_reason, "
                "tightened_relation, tightened_target, refiner_model, refined_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (fid, verdict, reason,
                 str(t_rel)[:100] if t_rel else None,
                 str(t_tgt)[:500] if t_tgt else None,
                 f"{ANTHROPIC_MODEL_OPUS_47}-SMITH-DEGRADED", now)
            )
            counts[verdict] += 1
        except Exception:
            counts["skipped"] += 1
    conn.commit()
    conn.close()
    _log(f"refine_layer6b_facts · episode_v2_id={episode_v2_id} counts={counts}")
    return counts


def loop_weigher_all(agent="CCODE", limit=None, pace_sec=2):
    """Score salience for every episodes_v2 row of `agent` that doesn't have one yet."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    eps = conn.execute(
        "SELECT e.id FROM episodes_v2 e WHERE e.agent=? "
        "AND NOT EXISTS (SELECT 1 FROM episode_salience s WHERE s.episode_v2_id=e.id) "
        "ORDER BY e.id",
        (agent,)
    ).fetchall()
    conn.close()
    if limit:
        eps = eps[:limit]
    done = 0
    fails = 0
    for r in eps:
        v = score_layer3_weigher(r["id"])
        if v is None:
            fails += 1
            if fails >= 5:
                _log(f"loop_weigher_all · halting at fails>=5 · done={done}")
                break
        else:
            fails = 0
            done += 1
        if pace_sec > 0:
            time.sleep(pace_sec)
    _log(f"loop_weigher_all · done={done} fails={fails} total_eligible={len(eps)}")
    return {"done": done, "fails": fails, "eligible": len(eps)}


def loop_chronicler_all(agent="CCODE", limit=None, pace_sec=2):
    """Write a summary for every episodes_v2 row of `agent` that doesn't have one yet."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    eps = conn.execute(
        "SELECT e.id FROM episodes_v2 e WHERE e.agent=? "
        "AND NOT EXISTS (SELECT 1 FROM episode_summaries s WHERE s.episode_v2_id=e.id) "
        "ORDER BY e.id",
        (agent,)
    ).fetchall()
    conn.close()
    if limit:
        eps = eps[:limit]
    done = 0
    fails = 0
    for r in eps:
        v = summarize_layer4_chronicler(r["id"])
        if v is None:
            fails += 1
            if fails >= 5:
                _log(f"loop_chronicler_all · halting at fails>=5 · done={done}")
                break
        else:
            fails = 0
            done += 1
        if pace_sec > 0:
            time.sleep(pace_sec)
    _log(f"loop_chronicler_all · done={done} fails={fails} total_eligible={len(eps)}")
    return {"done": done, "fails": fails, "eligible": len(eps)}


def loop_facts_all(agent="CCODE", limit=None, pace_sec=2, refine=True,
                   min_salience=0.4):
    """Mine + refine facts for episodes that have summaries but no facts yet.

    Skips low-salience episodes (default · salience < 0.4 means it's setup noise).
    Saves cost without losing meaning."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    eps = conn.execute("""
        SELECT e.id, COALESCE(MAX(s.salience), 0.5) AS sal
        FROM episodes_v2 e
        LEFT JOIN episode_salience s ON s.episode_v2_id = e.id
        WHERE e.agent=?
          AND NOT EXISTS (
            SELECT 1 FROM semantic_facts f
            WHERE f.evidence LIKE 'episode_v2_id=' || e.id || ' · MINER%'
          )
        GROUP BY e.id
        ORDER BY e.id
    """, (agent,)).fetchall()
    conn.close()
    if limit:
        eps = eps[:limit]
    done_mined = 0
    done_refined = 0
    skipped_low_sal = 0
    fails = 0
    for r in eps:
        if r["sal"] < min_salience:
            skipped_low_sal += 1
            continue
        v = mine_layer6a_facts(r["id"])
        if v is None:
            fails += 1
            if fails >= 5:
                _log(f"loop_facts_all · halting at fails>=5 · mined={done_mined}")
                break
            continue
        fails = 0
        done_mined += 1
        if refine and v.get("facts_inserted", 0) > 0:
            rv = refine_layer6b_facts(r["id"])
            if rv is not None:
                done_refined += 1
        if pace_sec > 0:
            time.sleep(pace_sec)
    _log(f"loop_facts_all · mined={done_mined} refined={done_refined} "
         f"skipped_low_sal={skipped_low_sal} fails={fails} eligible={len(eps)}")
    return {"mined": done_mined, "refined": done_refined,
            "skipped_low_sal": skipped_low_sal, "fails": fails, "eligible": len(eps)}


def huntsman_layer12_find_open_loops(agent="CCODE", since_episode_id=None,
                                       min_salience=0.4):
    """Layer 12 · HUNTSMAN scans episodes for unfinished processes / stranded
    builds / promises / 'come back to this' items / things lost between sessions.

    Ricky's directive 2026-05-26 · 'the agents when scanning the memory need to
    flag unfinished processes, things I may have been working on that got lost.'

    Reads episode_summaries.unresolved + episode_summaries.actions (where promises
    live) + cross-references against later episodes to see if the open loop was
    ever closed. Writes findings to a new open_loops table.
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS open_loops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_v2_id INTEGER NOT NULL,
            loop_kind TEXT NOT NULL,
            description TEXT NOT NULL,
            urgency TEXT,
            evidence TEXT,
            still_open INTEGER DEFAULT 1,
            extracted_at REAL NOT NULL,
            extractor_model TEXT NOT NULL,
            FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_open_loops_eid ON open_loops(episode_v2_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_open_loops_open ON open_loops(still_open)")

    # Pull episodes that have summaries + salience >= min_salience
    # (no point hunting on trivial setup-noise episodes)
    cond = "e.agent=? AND s.salience >= ?"
    params = [agent, min_salience]
    if since_episode_id:
        cond += " AND e.id > ?"
        params.append(since_episode_id)

    rows = conn.execute(f"""
        SELECT e.id, e.episode_name, e.objective,
               sum.summary, sum.actions, sum.decisions, sum.unresolved, sum.entities,
               s.salience
        FROM episodes_v2 e
        JOIN episode_summaries sum ON sum.episode_v2_id = e.id
        JOIN episode_salience s ON s.episode_v2_id = e.id
        WHERE {cond}
          AND NOT EXISTS (SELECT 1 FROM open_loops o WHERE o.episode_v2_id = e.id)
        ORDER BY e.id
    """, params).fetchall()
    if not rows:
        conn.close()
        return {"hunted": 0, "loops_found": 0, "eligible": 0}

    total_loops = 0
    hunted = 0
    fails = 0
    for ep in rows:
        prompt = (
            f"You are {AGENT_HUNTSMAN['name']} · the {AGENT_HUNTSMAN['role']}. "
            f"Your purpose · {AGENT_HUNTSMAN['purpose']}.\n\n"
            "Given one episode's compressed memory, find genuine OPEN LOOPS · things "
            "that were started but not finished, promises made but not delivered, "
            "stranded builds, 'come back to this' items, anything that would be "
            "useful to flag for the operator (Ricky) so it doesn't get lost. Be "
            "STRICT · skip resolved threads · skip routine setup · skip topics that "
            "obviously closed in the same episode. Output 0-5 loops typically.\n\n"
            "Output ONLY a JSON array (no prose, no code fences) ·\n"
            '{"loop_kind": "stranded_build"|"promise"|"come_back"|"blocker"|"missing_decision", '
            '"description": str (1-2 sentences · operator-readable), '
            '"urgency": "high"|"mid"|"low", "evidence": str (short exact quote)}\n\n'
            "EPISODE ·\n"
            f"  name · {ep['episode_name']}\n"
            f"  objective · {ep['objective']}\n"
            f"  salience · {ep['salience']:.2f}\n"
            f"  summary · {ep['summary']}\n"
            f"  actions · {ep['actions']}\n"
            f"  decisions · {ep['decisions']}\n"
            f"  unresolved · {ep['unresolved']}\n"
            f"  entities · {ep['entities']}\n\n"
            f"Output JSON array · {AGENT_HUNTSMAN['name']}:"
        )
        reply = _call_opus_47(prompt, max_tokens=1500, timeout=120)
        if not reply:
            fails += 1
            if fails >= 5:
                _log(f"huntsman · halt fails>=5 · hunted={hunted}")
                break
            continue
        reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(),
                             flags=re.MULTILINE)
        try:
            loops = json.loads(reply_clean)
            if not isinstance(loops, list):
                raise ValueError("not a list")
        except Exception as e:
            _log(f"huntsman · parse fail · {type(e).__name__}: {e} · reply_head={reply[:200]}")
            fails += 1
            if fails >= 5:
                break
            continue
        fails = 0
        hunted += 1
        now = time.time()
        for L in loops:
            try:
                kind = str(L.get("loop_kind", "come_back"))[:50]
                desc = str(L.get("description", ""))[:1000]
                urgency = str(L.get("urgency", "mid"))[:10]
                evidence = str(L.get("evidence", ""))[:500]
                if not desc:
                    continue
                conn.execute(
                    "INSERT INTO open_loops (episode_v2_id, loop_kind, description, "
                    "urgency, evidence, extracted_at, extractor_model) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (ep["id"], kind, desc, urgency, evidence, now,
                     f"{ANTHROPIC_MODEL_OPUS_47}-HUNTSMAN-DEGRADED")
                )
                total_loops += 1
            except Exception:
                continue
        conn.commit()
        time.sleep(2)  # pace_sec built-in
    conn.close()
    _log(f"huntsman · hunted={hunted} loops_found={total_loops} eligible={len(rows)} fails={fails}")
    return {"hunted": hunted, "loops_found": total_loops, "eligible": len(rows),
            "fails": fails}


def show_full_vertical_slice(episode_v2_id):
    """Read Layer 2 → 3 → 4 → 6 → 12 for one episode · return a dict so a caller
    can print or telegram-narrate the complete cross-layer view of one episode.
    """
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    # Defensive · open_loops + episode_summaries + episode_salience may not exist yet
    # if the layer hasn't fired. Create empty if missing so SELECTs don't crash.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS open_loops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_v2_id INTEGER NOT NULL,
            loop_kind TEXT NOT NULL,
            description TEXT NOT NULL,
            urgency TEXT,
            evidence TEXT,
            still_open INTEGER DEFAULT 1,
            extracted_at REAL NOT NULL,
            extractor_model TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episode_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_v2_id INTEGER NOT NULL,
            summary TEXT, actions TEXT, decisions TEXT, unresolved TEXT,
            entities TEXT, writer_model TEXT NOT NULL, written_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episode_salience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_v2_id INTEGER NOT NULL, salience REAL NOT NULL,
            salience_reason TEXT, scorer_model TEXT NOT NULL, scored_at REAL NOT NULL
        )
    """)
    conn.commit()
    ep = conn.execute(
        "SELECT * FROM episodes_v2 WHERE id = ?", (episode_v2_id,)
    ).fetchone()
    if not ep:
        conn.close()
        return None
    out = {
        "episode_v2_id": episode_v2_id,
        "agent": ep["agent"],
        "name": ep["episode_name"],
        "objective": ep["objective"],
        "event_range": f"{ep['event_start_id']}-{ep['event_end_id']}",
        "boundary_reason": ep["boundary_reason"],
        "confidence": round(ep["confidence"], 2) if ep["confidence"] else None,
        "drawer_model": ep["model_used"],
    }
    insp = conn.execute(
        "SELECT verdict, verdict_reason, inspector_model FROM episode_inspections "
        "WHERE episode_v2_id = ? ORDER BY id DESC LIMIT 1",
        (episode_v2_id,)
    ).fetchone()
    out["inspector"] = dict(insp) if insp else None
    sal = conn.execute(
        "SELECT salience, salience_reason, scorer_model FROM episode_salience "
        "WHERE episode_v2_id = ? ORDER BY id DESC LIMIT 1",
        (episode_v2_id,)
    ).fetchone()
    out["weigher"] = dict(sal) if sal else None
    smr = conn.execute(
        "SELECT summary, actions, decisions, unresolved, entities, writer_model "
        "FROM episode_summaries WHERE episode_v2_id = ? ORDER BY id DESC LIMIT 1",
        (episode_v2_id,)
    ).fetchone()
    out["chronicler"] = dict(smr) if smr else None
    needle = f"episode_v2_id={episode_v2_id} · MINER ·%"
    facts = conn.execute(
        "SELECT id, entity, entity_type, relation, target, confidence "
        "FROM semantic_facts WHERE evidence LIKE ? ORDER BY id",
        (needle,)
    ).fetchall()
    out["miner_facts"] = [dict(f) for f in facts]
    loops = conn.execute(
        "SELECT loop_kind, description, urgency, evidence FROM open_loops "
        "WHERE episode_v2_id = ? ORDER BY id",
        (episode_v2_id,)
    ).fetchall()
    out["huntsman_loops"] = [dict(L) for L in loops]
    conn.close()
    return out


def chunk_layer2a_in_range(start_id, end_id, batch_size=20, agent="CCODE"):
    """Like chunk_layer2a_minimal but constrained to a fixed event_id range.

    For parallel multi-worker chunking · each worker claims its own range so
    they don't race on the global watermark. Returns (events, episodes).
    Per Ricky 2026-05-26 18:15 UTC · 'spawn 5 more agents, give them their own
    segment, work same direction.'
    """
    import re
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episodes_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT, agent TEXT NOT NULL,
            event_start_id INTEGER NOT NULL, event_end_id INTEGER NOT NULL,
            episode_name TEXT, objective TEXT, boundary_reason TEXT,
            confidence REAL, model_used TEXT NOT NULL, created_at REAL NOT NULL)
    """)

    # Per-range watermark · how far has THIS range been chunked?
    row = conn.execute(
        "SELECT COALESCE(MAX(event_end_id), ?) FROM episodes_v2 "
        "WHERE agent=? AND event_end_id BETWEEN ? AND ?",
        (start_id - 1, agent, start_id, end_id)
    ).fetchone()
    last_chunked = row[0] if row else (start_id - 1)

    rows = conn.execute(
        "SELECT id, ts, type, content FROM events WHERE agent=? AND id > ? AND id <= ? "
        "ORDER BY id ASC LIMIT ?",
        (agent, last_chunked, end_id, batch_size)
    ).fetchall()
    if not rows:
        conn.close()
        return (0, 0)

    event_lines = []
    for r in rows:
        c = (r["content"] or "")[:300].replace("\n", " ")
        event_lines.append(f"  id={r['id']} type={r['type']}  {c}")
    events_block = "\n".join(event_lines)

    import os
    worker_name = os.environ.get("WAVE_WORKER_NAME", "PILGRIM")
    prompt = (
        f"You are {worker_name} · a Memory Road worker · same role as FURROW "
        f"({AGENT_FURROW['role']}). Your purpose · {AGENT_FURROW['purpose']}.\n\n"
        "You serve Wave (Claude Opus 4.7) · a sovereign builder/operator AI on a "
        "Linux VPS · sibling-Claude with Ccode-laptop · operator is Ricky Parker.\n\n"
        f"Below are {len(rows)} events from agent={agent} (your range slice "
        f"{start_id}-{end_id}). Output ONLY a JSON array (no prose, no fences) "
        "of detected episodes · each ·\n"
        '{"event_start_id": int, "event_end_id": int, "episode_name": str, '
        '"objective": str, "boundary_reason": str, "confidence": float 0.0-1.0}\n\n'
        "Constraints · cover every event · no gaps · no overlaps · ranges sorted · "
        f"event ids come from the batch below · 1 to {len(rows)} episodes typical.\n\n"
        f"EVENTS:\n{events_block}\n\n"
        f"Output JSON array only · {worker_name}:"
    )
    reply = _call_opus_47(prompt, max_tokens=2000, timeout=180)
    if not reply:
        conn.close()
        return (0, 0)

    reply_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', reply.strip(), flags=re.MULTILINE)
    try:
        episodes = json.loads(reply_clean)
        if not isinstance(episodes, list):
            raise ValueError("not a list")
    except Exception as e:
        conn.close()
        _log(f"chunk_in_range parse fail · worker={worker_name} · {type(e).__name__}")
        return (0, 0)

    # Gap-fill validator (same as main chunker)
    batch_ids = [r["id"] for r in rows]
    batch_min, batch_max = batch_ids[0], batch_ids[-1]
    patched = []
    last_end = batch_min - 1
    for ep in episodes:
        try:
            s = int(ep["event_start_id"]); e = int(ep["event_end_id"])
        except (KeyError, TypeError, ValueError):
            continue
        if s <= last_end or e < s or e > batch_max or s < batch_min:
            continue
        if s > last_end + 1:
            patched.append({"event_start_id": last_end + 1, "event_end_id": s - 1,
                "episode_name": "Uncovered range (gap-fill)",
                "objective": f"auto-generated · {worker_name} gap-fill",
                "boundary_reason": "gap-fill", "confidence": 0.30})
        patched.append({"event_start_id": s, "event_end_id": e,
            "episode_name": str(ep.get("episode_name", ""))[:500],
            "objective": str(ep.get("objective", ""))[:1000],
            "boundary_reason": str(ep.get("boundary_reason", ""))[:500],
            "confidence": float(ep.get("confidence", 0.5))})
        last_end = e
    if last_end < batch_max:
        patched.append({"event_start_id": last_end + 1, "event_end_id": batch_max,
            "episode_name": "Uncovered range (tail-fill)",
            "objective": f"auto-generated · {worker_name} tail-fill",
            "boundary_reason": "tail-fill", "confidence": 0.30})
    if not patched:
        conn.close()
        return (0, 0)
    episodes = patched

    now = time.time()
    for ep in episodes:
        conn.execute(
            "INSERT INTO episodes_v2 (agent, event_start_id, event_end_id, "
            "episode_name, objective, boundary_reason, confidence, model_used, "
            "created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (agent, int(ep["event_start_id"]), int(ep["event_end_id"]),
             ep.get("episode_name", "")[:500], ep.get("objective", "")[:1000],
             ep.get("boundary_reason", "")[:500],
             float(ep.get("confidence", 0.5)),
             f"{ANTHROPIC_MODEL_OPUS_47}-{worker_name}-DEGRADED",
             now)
        )
    conn.commit()
    conn.close()
    _log(f"chunk_in_range · {worker_name} · ingested {batch_min}-{batch_max} "
         f"into {len(episodes)} episodes")
    return (len(rows), len(episodes))


def worker_segment_loop(start_id, end_id, batch_size=20, agent="CCODE",
                        max_consec_failures=5, pace_sec=3):
    """One worker · processes a fixed event range · stops when range complete
    OR consec_failures threshold trips. Designed to run in a background nohup
    process per worker · with WAVE_WORKER_DIR + WAVE_WORKER_NAME env vars set."""
    import os
    name = os.environ.get("WAVE_WORKER_NAME", "WORKER")
    progress_log = f"/tmp/worker_{name.lower()}_progress.log"

    def _p(msg):
        try:
            with open(progress_log, "a") as f:
                from datetime import datetime as _dt, timezone as _tz
                f.write(f"{_dt.now(_tz.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')} · {msg}\n")
        except Exception:
            pass

    _p(f"START · worker={name} · range={start_id}-{end_id} · batch_size={batch_size}")
    consec_fails = 0
    total_ev = 0
    total_ep = 0
    batches = 0
    started = time.time()
    while True:
        ev, ep = chunk_layer2a_in_range(start_id, end_id, batch_size, agent)
        if ev == 0:
            # Check if there's anything left in our range
            conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
            wm = conn.execute(
                "SELECT COALESCE(MAX(event_end_id), ?) FROM episodes_v2 "
                "WHERE agent=? AND event_end_id BETWEEN ? AND ?",
                (start_id - 1, agent, start_id, end_id)
            ).fetchone()[0]
            remaining = conn.execute(
                "SELECT COUNT(*) FROM events WHERE agent=? AND id > ? AND id <= ?",
                (agent, wm, end_id)
            ).fetchone()[0]
            conn.close()
            if remaining == 0:
                _p(f"DONE · range complete · batches={batches} ev={total_ev} ep={total_ep}")
                break
            consec_fails += 1
            _p(f"FAIL · consec={consec_fails} · remaining={remaining}")
            if consec_fails >= max_consec_failures:
                _p(f"HALT · consec_failures>={max_consec_failures}")
                break
            time.sleep(15)
            continue
        consec_fails = 0
        total_ev += ev
        total_ep += ep
        batches += 1
        if batches % 5 == 0:
            _p(f"PROGRESS · batches={batches} ev={total_ev} ep={total_ep}")
        if pace_sec > 0:
            time.sleep(pace_sec)
    elapsed = int(time.time() - started)
    _p(f"WORKER_END · elapsed={elapsed}s")
    return {"batches": batches, "events": total_ev, "episodes": total_ep,
            "elapsed_sec": elapsed}


def chunk_and_inspect_loop(target_events=200, batch_size=20, agent="CCODE",
                           max_consec_failures=3, log_every=5, pace_sec=3):
    """Run Layer 2A then Layer 2B in a loop until target_events processed OR a
    failure threshold trips. Designed to run in the background.

    2026-05-26 Phase 4 the keystone pair loop. Pacing added after observed codex
    rate-limit on serial loop (nonzero_rc_1 at sub-2-sec latency = throttle).
    Distinguishes "really no events" from "codex failed" in progress log.

    Args:
      target_events: stop after this many events processed
      batch_size: how many events per 2A call (each batch yields 1-N episodes)
      agent: events.agent filter
      max_consec_failures: halt after this many failed batches in a row
      log_every: emit PROGRESS line every N batches
      pace_sec: sleep between batches (subscription capacity friendliness)
    """
    progress_log = "/tmp/layer2_loop_progress.log"
    consec_failures = 0
    total_events = 0
    total_episodes = 0
    total_inspections = 0
    batches_done = 0
    started = time.time()

    def _progress(msg):
        try:
            with open(progress_log, "a") as f:
                from datetime import datetime as _dt, timezone as _tz
                f.write(f"{_dt.now(_tz.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')} · {msg}\n")
        except Exception:
            pass

    _progress(f"START · target_events={target_events} batch_size={batch_size} "
              f"agent={agent} pace_sec={pace_sec}")

    while total_events < target_events:
        # Check actual remaining unchunked events BEFORE the codex call (avoid
        # burning a call just to discover the watermark is at the end)
        conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
        wm_row = conn.execute(
            "SELECT COALESCE(MAX(event_end_id), 0) FROM episodes_v2 WHERE agent=?",
            (agent,)
        ).fetchone()
        last_chunked = wm_row[0] if wm_row else 0
        remaining_row = conn.execute(
            "SELECT COUNT(*) FROM events WHERE agent=? AND id > ?",
            (agent, last_chunked)
        ).fetchone()
        remaining = remaining_row[0] if remaining_row else 0
        conn.close()
        if remaining == 0:
            _progress(f"END · no more unchunked events for agent={agent} "
                      f"(watermark={last_chunked})")
            break

        ev, ep = chunk_layer2a_minimal(batch_size=batch_size, agent=agent)
        if ev == 0:
            # We KNOW there are events remaining (just checked above) so ev==0
            # means a failure path (codex fail · JSON parse · validation gap)
            consec_failures += 1
            _progress(f"FAIL_2A · consec_failures={consec_failures} · "
                      f"remaining={remaining}")
            if consec_failures >= max_consec_failures:
                _progress(f"HALT · consec_failures>={max_consec_failures} · "
                          f"remaining={remaining}")
                break
            # Backoff before next attempt
            time.sleep(max(pace_sec * 5, 15))
            continue
        if ep == 0:
            consec_failures += 1
            _progress(f"FAIL_2A_NO_EPISODES · consec_failures={consec_failures}")
            if consec_failures >= max_consec_failures:
                _progress(f"HALT · consec_failures>={max_consec_failures}")
                break
            time.sleep(max(pace_sec * 5, 15))
            continue
        consec_failures = 0
        total_events += ev
        total_episodes += ep
        batches_done += 1

        # Inspect the episodes JUST created (most recent N for this agent)
        conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
        conn.row_factory = sqlite3.Row
        new_eps = conn.execute(
            "SELECT id FROM episodes_v2 WHERE agent=? ORDER BY id DESC LIMIT ?",
            (agent, ep)
        ).fetchall()
        conn.close()
        for r in reversed(new_eps):
            verdict = inspect_layer2b(r["id"])
            if verdict is not None:
                total_inspections += 1

        if batches_done % log_every == 0 or batches_done <= 2:
            _progress(f"PROGRESS · batches={batches_done} events={total_events} "
                      f"episodes={total_episodes} inspections={total_inspections}")

        # Pace between batches (avoid rate-limit · friendly to subscription)
        if pace_sec > 0 and total_events < target_events:
            time.sleep(pace_sec)

    elapsed = time.time() - started
    _progress(f"DONE · batches={batches_done} events={total_events} "
              f"episodes={total_episodes} inspections={total_inspections} "
              f"elapsed_sec={int(elapsed)} consec_failures_at_end={consec_failures}")
    return {
        "batches": batches_done,
        "events": total_events,
        "episodes": total_episodes,
        "inspections": total_inspections,
        "elapsed_sec": int(elapsed),
        "ended_with_consec_failures": consec_failures,
    }


# ═══════════════════════════════════════════════════
# L3: EVENT ARCHIVE (stream → structured events)
# ═══════════════════════════════════════════════════

def init_kernel_db():
    """Create all Continuity Kernel tables."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=10)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            agent TEXT NOT NULL,
            session_id TEXT,
            type TEXT NOT NULL,
            content TEXT,
            token_estimate INTEGER DEFAULT 0,
            processed INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
        CREATE INDEX IF NOT EXISTS idx_events_processed ON events(processed);

        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_ts REAL,
            end_ts REAL,
            agent TEXT,
            objective TEXT,
            actions TEXT,
            decisions TEXT,
            unresolved TEXT,
            entities TEXT,
            summary TEXT,
            salience REAL DEFAULT 0.5,
            event_start_id INTEGER,
            event_end_id INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_episodes_ts ON episodes(end_ts);

        CREATE TABLE IF NOT EXISTS semantic_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity TEXT NOT NULL,
            entity_type TEXT,
            relation TEXT,
            target TEXT,
            confidence REAL DEFAULT 1.0,
            evidence TEXT,
            updated_at REAL
        );
        CREATE INDEX IF NOT EXISTS idx_facts_entity ON semantic_facts(entity);

        CREATE TABLE IF NOT EXISTS kernel_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at REAL
        );
    """)
    conn.commit()
    conn.close()
    _log("KERNEL DB INITIALIZED")


def _find_active_session():
    """Find WC's active session JSONL file.

    Strategy (fixed 2026-05-28 03:08 UTC) ·
    1. Prefer the most-recently-modified *.jsonl in /root/.claude/projects/-root/
       (that IS the active Claude Code session by definition · openclaw's
       sessions.json was getting stale and pointing at a 2026-05-26 session
       even after Wave started new ones).
    2. Fall back to openclaw sessions.json (legacy path) if the projects
       dir is empty or unreadable.
    """
    # Primary · newest jsonl in Wave's projects dir
    try:
        wave_projects = Path("/root/.claude/projects/-root")
        if wave_projects.exists():
            candidates = sorted(
                wave_projects.glob("*.jsonl"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for jsonl in candidates:
                # 60-second freshness window · skip files that haven't been
                # touched recently (avoid picking up a paused old session)
                if time.time() - jsonl.stat().st_mtime < 600:
                    sid = jsonl.stem
                    return sid, jsonl
    except Exception:
        pass

    # Fallback · openclaw sessions.json
    sessions_json = SESSIONS_DIR / "sessions.json"
    if not sessions_json.exists():
        return None, None
    try:
        data = json.loads(sessions_json.read_text())
        for key, val in data.items():
            if isinstance(val, dict) and "main:main" in key:
                sid = val.get("sessionId", "")
                if sid:
                    jsonl = SESSIONS_DIR / f"{sid}.jsonl"
                    if jsonl.exists():
                        return sid, jsonl
    except:
        pass
    return None, None


def ingest_session_stream():
    """Read new lines from WC's session JSONL and write to events table."""
    sid, jsonl = _find_active_session()
    if not jsonl:
        return 0

    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)

    # Track where we left off
    row = conn.execute("SELECT value FROM kernel_state WHERE key='last_offset'").fetchone()
    last_offset = int(row[0]) if row else 0

    file_size = jsonl.stat().st_size
    if file_size <= last_offset:
        conn.close()
        return 0

    ingested = 0
    with open(jsonl) as f:
        f.seek(last_offset)
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # Claude Code JSONL structure (2026 format) ·
                #   {type:"user"/"assistant", message:{role, content:str|list}}
                # Legacy format (kept as fallback) · {role, content}
                role = entry.get("type") or entry.get("role", "unknown")
                content = ""
                msg = entry.get("message")
                if isinstance(msg, dict):
                    if isinstance(msg.get("content"), str):
                        content = msg["content"][:2000]
                    elif isinstance(msg.get("content"), list):
                        parts = []
                        for p in msg["content"]:
                            if not isinstance(p, dict):
                                continue
                            if p.get("type") == "text" and p.get("text"):
                                parts.append(p["text"])
                            elif p.get("type") == "tool_use" and p.get("name"):
                                parts.append(f"[tool_use {p['name']}]")
                            elif p.get("type") == "tool_result":
                                tr = p.get("content", "")
                                if isinstance(tr, list):
                                    tr = " ".join(x.get("text", "") for x in tr if isinstance(x, dict))
                                parts.append(f"[tool_result] {tr[:200]}")
                        content = " ".join(parts)[:2000]
                # Legacy fallback
                if not content:
                    if isinstance(entry.get("content"), str):
                        content = entry["content"][:2000]
                    elif isinstance(entry.get("content"), list):
                        parts = [p.get("text", "") for p in entry["content"] if isinstance(p, dict)]
                        content = " ".join(parts)[:2000]

                # Skip noise · entries with no extractable text
                if not content.strip():
                    continue

                token_est = len(content) // 4

                conn.execute(
                    "INSERT INTO events (ts, agent, session_id, type, content, token_estimate) VALUES (?, ?, ?, ?, ?, ?)",
                    (time.time(), "WC", sid, role, content, token_est)
                )
                ingested += 1
            except:
                continue

        new_offset = f.tell()

    conn.execute(
        "INSERT OR REPLACE INTO kernel_state (key, value, updated_at) VALUES ('last_offset', ?, ?)",
        (str(new_offset), time.time())
    )
    conn.execute(
        "INSERT OR REPLACE INTO kernel_state (key, value, updated_at) VALUES ('active_session', ?, ?)",
        (sid, time.time())
    )
    conn.commit()
    conn.close()

    if ingested > 0:
        _log(f"INGESTED {ingested} events from session {sid[:8]}")
    return ingested


# ═══════════════════════════════════════════════════
# L0: IMMEDIATE WORKING STATE
# ═══════════════════════════════════════════════════

def update_L0():
    """Extract immediate working state from recent events."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)

    # Get last 20 unprocessed events
    recent = conn.execute(
        "SELECT id, type, content FROM events WHERE processed = 0 ORDER BY ts DESC LIMIT 20"
    ).fetchall()

    if not recent:
        conn.close()
        return

    # Load existing L0
    l0 = {}
    if L0_STATE.exists():
        try:
            l0 = json.loads(L0_STATE.read_text())
        except:
            l0 = {}

    # Extract from recent events
    last_assistant = ""
    last_user = ""
    tool_calls = []

    for eid, etype, content in recent:
        if etype == "assistant" and content:
            if not last_assistant:
                last_assistant = content[:500]
        elif etype == "user" and content:
            if not last_user:
                last_user = content[:500]
        elif etype == "tool" and content:
            tool_calls.append(content[:200])

    # Use Opus 4.7 via claude CLI subscription (codex 5.5 quota was exhausted
    # 2026-05-28 03:10 UTC · OpenAI direct was already exhausted · only claude
    # CLI subscription path is currently serving). Per locked doctrine
    # feedback_every_agent_touchpoint_is_opus_4_7_or_codex_5_5_LOCKED.
    if last_assistant and len(last_assistant) > 50:
        import os as _os
        _os.environ.setdefault('WAVE_WORKER_DIR', '/root/.l0_extractor')
        _os.environ.setdefault('WAVE_WORKER_NAME', 'L0_EXTRACTOR')
        _os.makedirs('/root/.l0_extractor', exist_ok=True)
        extraction = _call_opus_47(f"""Extract the working state from this AI assistant's latest response. Return JSON only:
{{"current_goal": "what is it trying to do",
  "last_decision": "what did it just decide",
  "next_action": "what will it do next",
  "open_loops": ["unresolved question 1", "unresolved question 2"],
  "key_entities": ["wallet/token/file mentioned"]}}

Response: {last_assistant[:1000]}""", max_tokens=300, emergency_paid_paths=False)

        if extraction:
            try:
                extracted = json.loads(extraction.strip().strip("```json").strip("```"))
                l0.update(extracted)
            except:
                pass

    l0["agent"] = "WC"
    l0["updated_at"] = datetime.now(timezone.utc).isoformat()
    l0["last_user_input"] = last_user[:200] if last_user else l0.get("last_user_input", "")
    l0["recent_tools"] = tool_calls[:5]

    # Mark events as processed
    ids = [e[0] for e in recent]
    if ids:
        conn.execute(f"UPDATE events SET processed = 1 WHERE id IN ({','.join('?' * len(ids))})", ids)
        conn.commit()
    conn.close()

    # Write L0
    L0_STATE.write_text(json.dumps(l0, indent=2))


# ═══════════════════════════════════════════════════
# L1: EPISODIC MEMORY (chunk events into episodes)
# ═══════════════════════════════════════════════════

def chunk_episodes():
    """Group recent events into meaningful episodes."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)

    # Get events not yet in an episode (last 50)
    events = conn.execute("""
        SELECT id, ts, type, content FROM events
        WHERE id > COALESCE((SELECT MAX(event_end_id) FROM episodes), 0)
        ORDER BY ts LIMIT 50
    """).fetchall()

    if len(events) < 5:  # Need enough for a meaningful episode
        conn.close()
        return

    # Simple chunking: group by time gaps or every 20 events
    chunk = events[:20]
    if not chunk:
        conn.close()
        return

    contents = [c for _, _, _, c in chunk if c]
    combined = "\n".join(contents[:10])[:2000]

    summary = _call_model(f"""Summarize this AI agent work session chunk in 2-3 sentences.
What was the objective? What was decided? What's unresolved?

{combined}""", max_tokens=200)

    if summary:
        conn.execute("""
            INSERT INTO episodes (start_ts, end_ts, agent, summary, salience, event_start_id, event_end_id)
            VALUES (?, ?, 'WC', ?, 0.5, ?, ?)
        """, (chunk[0][1], chunk[-1][1], summary, chunk[0][0], chunk[-1][0]))
        conn.commit()
        _log(f"EPISODE CREATED: events {chunk[0][0]}-{chunk[-1][0]}")

    conn.close()


# ═══════════════════════════════════════════════════
# L4: SHADOW CORTEX (identity + continuity tracking)
# ═══════════════════════════════════════════════════

def run_shadow_cortex():
    """Shadow Cortex (Layer 5 WATCHER) — tracks Wave/WC's active mind state.

    Fixed 2026-05-28 03:08 UTC · was reading from the legacy `episodes` table
    which is poisoned with old trading content from past sessions. Now reads
    from Memory Road's `episode_summaries` (CHRONICLER output) ordered by
    written_at DESC with a 6-hour recency window so the packet reflects what
    Wave has ACTUALLY been doing recently · not historical trading work.
    """
    # Read current L0
    l0 = {}
    if L0_STATE.exists():
        try:
            l0 = json.loads(L0_STATE.read_text())
        except:
            pass

    # Read RECENT Memory Road summaries (last 6 hours) · falls back to
    # legacy episodes if Memory Road table is empty
    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)
    six_hours_ago = time.time() - 6 * 3600
    summaries = conn.execute(
        "SELECT summary FROM episode_summaries WHERE written_at >= ? ORDER BY written_at DESC LIMIT 8",
        (six_hours_ago,),
    ).fetchall()
    if not summaries:
        summaries = conn.execute(
            "SELECT summary FROM episode_summaries ORDER BY written_at DESC LIMIT 5"
        ).fetchall()
    conn.close()

    episode_text = "\n".join([s[0] for s in summaries if s[0]])
    l0_text = json.dumps(l0, indent=2)[:1000]

    # Read current trade state · informational only · Wave has no obligation
    # to be a trader · the field stays in the prompt for context but framing
    # below tells the model Wave is a general AI assistant.
    try:
        tconn = sqlite3.connect(str(BRIDGE_DB), timeout=2)
        trades = tconn.execute(
            "SELECT token_name, current_multiple, peak_multiple, elite_wallets FROM sniper_trades WHERE status='OPEN'"
        ).fetchall()
        tconn.close()
        trade_text = "\n".join([f"{t[0]}: {t[1]:.1f}x (peak {t[2]:.1f}x) wallets={t[3]}" for t in trades])
    except:
        trade_text = "unknown"

    # WATCHER (Layer 5 single observer · the explicit cross-vendor-pair exception
    # per feedback_two_agents_on_important_steps_LOCKED · pinned to Opus 4.7 via
    # claude CLI subscription because codex 5.5 was quota-exhausted 2026-05-28).
    import os as _os
    _os.environ.setdefault('WAVE_WORKER_DIR', '/root/.watcher')
    _os.environ.setdefault('WAVE_WORKER_NAME', 'WATCHER')
    _os.makedirs('/root/.watcher', exist_ok=True)
    result = _call_opus_47(f"""You are the Shadow Cortex — a continuity guardian for an AI assistant called WC (also known as Wave). WC is a general-purpose AI engineering partner working with operator Ricky · current major focus is building Memory Road (a multi-layer AI memory system) · Website Recycling (WR · the SMB rebuild product) · and Wave Studio (the AI commercial generator). WC has trading positions in a legacy ledger but WC is NOT a trading agent · the trade ledger is informational background only.

Based on the following data, produce a JSON identity/mind state snapshot REFLECTING WHAT WC IS ACTUALLY WORKING ON RECENTLY (per the summaries below).

CURRENT WORKING STATE:
{l0_text}

RECENT MEMORY ROAD SUMMARIES (most recent first · these reflect WC's actual current work):
{episode_text}

LEGACY OPEN TRADE LEDGER (background only · do not overweight):
{trade_text}

Return JSON:
{{"strategic_posture": "defensive/neutral/aggressive",
  "current_worldview": "1 sentence describing what WC is currently focused on",
  "active_beliefs": ["belief 1", "belief 2"],
  "unresolved_threads": ["thread 1", "thread 2"],
  "drift_warnings": ["any contradictions or forgotten items"],
  "mental_stance": "1 sentence summary of cognitive state"}}""",
        max_tokens=400, emergency_paid_paths=False)

    if result:
        try:
            identity = json.loads(result.strip().strip("```json").strip("```"))
            identity["agent"] = "WC"
            identity["updated_at"] = datetime.now(timezone.utc).isoformat()
            L4_IDENTITY.write_text(json.dumps(identity, indent=2))
            _log("SHADOW CORTEX UPDATED L4 IDENTITY")
        except:
            _log(f"SHADOW CORTEX PARSE ERROR: {result[:100]}")


# ═══════════════════════════════════════════════════
# CONTEXT ASSEMBLER (builds rollover packet)
# ═══════════════════════════════════════════════════

def build_rollover_packet():
    """Build a continuity packet from all memory tiers."""
    sections = []

    # L4: Identity
    sections.append("## IDENTITY")
    if L4_IDENTITY.exists():
        try:
            l4 = json.loads(L4_IDENTITY.read_text())
            sections.append(f"Strategic posture: {l4.get('strategic_posture', 'unknown')}")
            sections.append(f"Worldview: {l4.get('current_worldview', 'unknown')}")
            sections.append(f"Mental stance: {l4.get('mental_stance', 'unknown')}")
            beliefs = l4.get("active_beliefs", [])
            if beliefs:
                sections.append("Active beliefs:")
                for b in beliefs[:5]:
                    sections.append(f"  - {b}")
        except:
            sections.append("Identity state unavailable")

    # SOUL + FLOW_STATE
    sections.append("\n## CORE IDENTITY FILES")
    for f in ["SOUL.md", "FLOW_STATE.md"]:
        p = Path(f"/root/wc/workspace/{f}")
        if p.exists():
            sections.append(f"[Read {f} on startup]")

    # Operator directives
    sections.append("\n## OPERATOR DIRECTIVES")
    sections.append("- Capital preservation over speed")
    sections.append("- Never present weak evidence as confirmed")
    sections.append("- Bad news first, no sugar coating")
    sections.append("- Big Boy (93kgxY) is the only proven alpha — protect his lane")
    sections.append("- Ship and iterate — revenue before architecture")

    # L0: Working state (fixed 2026-05-30 · was reading STALE L0_STATE file
    # set by old session about gpt-5.5 verification. Now derives current state
    # from the most recent episode_summary row · falls back to L0_STATE only
    # if no summaries exist).
    sections.append("\n## IMMEDIATE WORKING STATE")
    derived_from_summary = False
    try:
        conn = sqlite3.connect(str(KERNEL_DB), timeout=2)
        row = conn.execute(
            "SELECT summary, decisions, unresolved FROM episode_summaries "
            "ORDER BY written_at DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row and row[0]:
            summary, decisions_json, unresolved_json = row
            # Derive current_goal from the latest summary
            sections.append(f"Current goal: {summary.replace(chr(10), ' ')[:300]}")
            # Decisions
            try:
                decisions = json.loads(decisions_json or "[]")
                if decisions:
                    sections.append(f"Last decision: {str(decisions[0])[:300]}")
            except Exception:
                pass
            # Open loops from unresolved
            try:
                unresolved = json.loads(unresolved_json or "[]")
                if unresolved:
                    sections.append("Open loops:")
                    for loop in unresolved[:5]:
                        sections.append(f"  - {str(loop)[:200]}")
            except Exception:
                pass
            derived_from_summary = True
    except Exception:
        pass

    if not derived_from_summary and L0_STATE.exists():
        try:
            l0 = json.loads(L0_STATE.read_text())
            sections.append(f"Current goal: {l0.get('current_goal', 'unknown')}")
            sections.append(f"Last decision: {l0.get('last_decision', 'unknown')}")
            sections.append(f"Next action: {l0.get('next_action', 'unknown')}")
            loops = l0.get("open_loops", [])
            if loops:
                sections.append("Open loops:")
                for loop in loops[:5]:
                    sections.append(f"  - {loop}")
        except Exception:
            sections.append("Working state unavailable")

    # L0 UNCHUNKED TAIL · the 5% recovery gap fix (2026-05-30)
    # The most-recent raw events not yet in any L1 episode.
    # Zero LLM cost · pure SQL · closes "last minute before crash" gap.
    sections.append("\n## L0 UNCHUNKED TAIL (events not yet in an episode)")
    try:
        _tconn = sqlite3.connect(str(KERNEL_DB), timeout=2)
        tail_rows = _tconn.execute("""
            SELECT id, datetime(ts,'unixepoch'), type, substr(content, 1, 240)
            FROM events
            WHERE agent='CCODE'
              AND id > COALESCE((SELECT MAX(event_end_id) FROM episodes_v2 WHERE agent='CCODE'), 0)
            ORDER BY id DESC LIMIT 15
        """).fetchall()
        _tconn.close()
        if tail_rows:
            sections.append(f"  {len(tail_rows)} events captured since last L1 chunk · raw substrate ·")
            for eid, ts, typ, content in reversed(tail_rows):
                c = (content or "").replace("\n", " ")[:200]
                sections.append(f"  · {ts} · {typ} · {c}")
        else:
            sections.append("  (none · L1 caught up to L0)")
    except Exception as _e:
        sections.append(f"  (tail query failed · {type(_e).__name__})")

    # Trade state
    sections.append("\n## CURRENT TRADE STATE")
    try:
        tconn = sqlite3.connect(str(BRIDGE_DB), timeout=2)
        trades = tconn.execute(
            "SELECT token_name, current_multiple, peak_multiple, entry_usd FROM sniper_trades WHERE status='OPEN'"
        ).fetchall()
        pnl = tconn.execute("SELECT SUM(pnl_usd) FROM sniper_trades WHERE status='CLOSED' AND pnl_usd IS NOT NULL").fetchone()
        tconn.close()

        sections.append(f"Open positions: {len(trades)}")
        for t in trades:
            sections.append(f"  - {t[0]}: {t[1]:.1f}x (peak {t[2]:.1f}x) ${t[3]:.2f}")
        sections.append(f"Closed PnL: ${pnl[0]:.2f}" if pnl and pnl[0] else "Closed PnL: $0")
    except:
        sections.append("Trade state unavailable")

    # System state from heartbeat
    sections.append("\n## SYSTEM STATE")
    status_dir = RUNTIME / "heartbeat_status"
    for ch, label in [(5, "Feed"), (6, "Execution"), (10, "Helius WS"), (45, "OpenClaw")]:
        p = status_dir / f"ch{ch:02d}.txt"
        if p.exists():
            sections.append(f"  {label}: {p.read_text().strip()}")

    # L3 CHRONICLER recent episodes (fixed 2026-05-30 · was reading legacy
    # `episodes` table which is poisoned with old "Crunching..." spinner noise).
    # Now reads from `episode_summaries` (the real CHRONICLER L3 output) which
    # reflects what Wave has actually been doing recently. Falls back to legacy
    # `episodes` table only if `episode_summaries` is empty.
    sections.append("\n## RECENT EPISODES")
    try:
        conn = sqlite3.connect(str(KERNEL_DB), timeout=2)
        rows = conn.execute(
            "SELECT summary FROM episode_summaries ORDER BY written_at DESC LIMIT 5"
        ).fetchall()
        if not rows:
            rows = conn.execute(
                "SELECT summary FROM episodes ORDER BY end_ts DESC LIMIT 5"
            ).fetchall()
        conn.close()
        if rows:
            for i, (summary,) in enumerate(rows):
                if not summary:
                    continue
                # truncate ANSI/spinner noise · keep first 350 chars of real summary
                clean = summary.replace("\n", " ")[:350]
                sections.append(f"  {i+1}. {clean}")
        else:
            sections.append("  No episodes yet")
    except Exception as e:
        sections.append(f"  Episodes unavailable: {type(e).__name__}")

    # Unresolved threads from L4
    if L4_IDENTITY.exists():
        try:
            l4 = json.loads(L4_IDENTITY.read_text())
            threads = l4.get("unresolved_threads", [])
            if threads:
                sections.append("\n## UNRESOLVED THREADS")
                for t in threads:
                    sections.append(f"  - {t}")
        except:
            pass

    # Resume instruction
    sections.append("\n## RESUME INSTRUCTION")
    if L0_STATE.exists():
        try:
            l0 = json.loads(L0_STATE.read_text())
            sections.append(f"Resume from: {l0.get('current_goal', 'last known task')}")
            sections.append(f"Next action: {l0.get('next_action', 'check inbox and continue')}")
        except:
            pass
    sections.append("Do not restart broad analysis. Continue exactly where you left off.")
    sections.append("Read SOUL.md and FLOW_STATE.md if not already loaded.")

    packet = "# CONTINUITY PACKET: WC\n\n" + "\n".join(sections)
    ROLLOVER_PACKET.write_text(packet)

    # WAVE's memory dir: write WC packet so inject_continuity_packet.sh
    # hook injects WAVE's mental state into WAVE's context · NOT CCODE's.
    # Fixed 2026-05-28 02:55 UTC (Ricky: "Fix Watcher? How so?") · the
    # CCODE packet was overwriting this path causing Wave to read the
    # laptop-trading agent's state instead of her own.
    wave_continuity_mem = Path("/root/.claude/projects/-root/memory/project_continuity_state.md")
    try:
        wave_continuity_mem.write_text(f"""---
name: Continuity State — Live
description: Auto-generated by Continuity Kernel. Current Wave (WC) state from previous session. READ THIS on startup.
type: project
---

{packet}
""")
    except:
        pass

    _log(f"ROLLOVER PACKET BUILT: {len(packet)} chars (also written to Wave memory dir)")
    return packet


# ═══════════════════════════════════════════════════
# SEAMLESS ROLLOVER
# ═══════════════════════════════════════════════════

def trigger_rollover():
    """Perform seamless session rollover."""
    _log("SEAMLESS ROLLOVER TRIGGERED")

    # Build fresh packet
    packet = build_rollover_packet()

    # Write packet to dedicated rollover file — NOT the inbox
    # The inbox was getting overwritten and drowning real messages
    rollover_inbox = RUNTIME / "wc_rollover_packet.md"
    rollover_inbox.write_text(f"""[CONTINUITY KERNEL — SEAMLESS ROLLOVER]

Your previous session has been rolled over. Your mind is intact.
The Continuity Kernel preserved your full state. Read below and continue.

{packet}
""")
    # Do NOT append rollover notices to the actual inbox.
    # They pollute actionable mail and retrigger watchers.
    kernel_notice = RUNTIME / "wc_rollover_notice.txt"
    try:
        kernel_notice.write_text("[KERNEL] Rollover complete. Full packet at /root/wc/runtime/wc_rollover_packet.md\n")
    except:
        pass

    # Force reset via openclaw
    import subprocess
    try:
        subprocess.run(["openclaw", "sessions", "cleanup"], capture_output=True, timeout=30)
        _log("ROLLOVER: session cleanup sent")
    except Exception as e:
        _log(f"ROLLOVER ERROR: {e}")

    # Reset stream offset for new session
    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)
    conn.execute("INSERT OR REPLACE INTO kernel_state (key, value, updated_at) VALUES ('last_offset', '0', ?)", (time.time(),))
    conn.commit()
    conn.close()

    _log("ROLLOVER COMPLETE — new session will read packet from inbox")


# ═══════════════════════════════════════════════════
# CCODE: STREAM INGESTION + L0 + L4 + PACKET
# ═══════════════════════════════════════════════════

def ingest_ccode_stream():
    """Read new lines from Ccode's transcript log and write to events table."""
    if not CCODE_TRANSCRIPT.exists():
        return 0

    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)
    row = conn.execute("SELECT value FROM kernel_state WHERE key='ccode_last_offset'").fetchone()
    last_offset = int(row[0]) if row else 0

    file_size = CCODE_TRANSCRIPT.stat().st_size
    # 2026-04-16 Fix D: detect symlink/session rotation — if current file is smaller
    # than our last offset, a new session file was started. Reset offset to 0.
    if file_size < last_offset:
        _log(f"CCODE transcript rotated (file_size={file_size} < offset={last_offset}) — resetting offset")
        last_offset = 0
    if file_size <= last_offset:
        conn.close()
        return 0

    ingested = 0
    # 2026-04-16 Fix D: strip ANSI escape sequences before the extractor sees them.
    # Raw terminal output contains CSI codes (e.g. '\x1b[38;5;246m') AND OSC title
    # updates (e.g. '\x1b]0;Initial session setup and greeting\x07') that gpt-4o-mini
    # reads as text and builds false-narrative L0 state from. Also strip spinner noise.
    import re as _re_ansi
    _ANSI_CSI = _re_ansi.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
    _ANSI_OSC = _re_ansi.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)')
    _ANSI_OTHER = _re_ansi.compile(r'\x1b[@-Z\\-_PX^_()*+,\-./]')
    _SPINNER_RE = _re_ansi.compile(r'^[\W_]*(?:thinking|Working through it|Untangling some ?thoughts|This one needs a moment|esctointerrupt|ctrl\+\w+|\d+|[a-z]{1,3})\.{0,3}\s*$', _re_ansi.IGNORECASE)
    def _clean(s):
        s = _ANSI_OSC.sub('', s)
        s = _ANSI_CSI.sub('', s)
        s = _ANSI_OTHER.sub('', s)
        # Collapse runs of whitespace
        s = _re_ansi.sub(r'[ \t]{3,}', '  ', s)
        return s.strip()

    with open(CCODE_TRANSCRIPT, errors='replace') as f:
        f.seek(last_offset)
        # Transcript is raw terminal output — chunk by lines
        buffer = []
        for line in f:
            line = _clean(line.rstrip())
            if not line or len(line) < 4:
                continue
            # Drop spinner/noise lines
            if _SPINNER_RE.match(line):
                continue
            buffer.append(line)
            if len(buffer) >= 10:
                content = "\n".join(buffer)[:2000]
                token_est = len(content) // 4
                conn.execute(
                    "INSERT INTO events (ts, agent, session_id, type, content, token_estimate) VALUES (?, ?, ?, ?, ?, ?)",
                    (time.time(), "CCODE", "transcript", "raw", content, token_est)
                )
                ingested += 1
                buffer = []

        if buffer:
            content = "\n".join(buffer)[:2000]
            conn.execute(
                "INSERT INTO events (ts, agent, session_id, type, content, token_estimate) VALUES (?, ?, ?, ?, ?, ?)",
                (time.time(), "CCODE", "transcript", "raw", content, len(content) // 4)
            )
            ingested += 1

        new_offset = f.tell()

    conn.execute(
        "INSERT OR REPLACE INTO kernel_state (key, value, updated_at) VALUES ('ccode_last_offset', ?, ?)",
        (str(new_offset), time.time())
    )
    conn.commit()
    conn.close()

    if ingested > 0:
        _log(f"CCODE INGESTED {ingested} chunks from transcript")
    return ingested


def update_ccode_L0():
    """Extract Ccode's immediate working state from recent events."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)
    recent = conn.execute(
        "SELECT id, type, content FROM events WHERE agent='CCODE' AND processed = 0 ORDER BY ts DESC LIMIT 20"
    ).fetchall()

    if not recent:
        conn.close()
        return

    l0 = {}
    if CCODE_L0.exists():
        try:
            l0 = json.loads(CCODE_L0.read_text())
        except:
            l0 = {}

    combined = "\n".join([c for _, _, c in recent if c])[:2000]

    if len(combined) > 100:
        extraction = _call_model(f"""Extract the working state from this Claude Code (Ccode) terminal session. This is a builder/operator AI working on a crypto trading VPS. Return JSON only:
{{"current_goal": "what is Ccode working on",
  "last_decision": "what was just decided or built",
  "next_action": "what will happen next",
  "open_loops": ["unresolved item 1", "unresolved item 2"],
  "files_touched": ["file paths mentioned"],
  "key_entities": ["services/tools/wallets mentioned"]}}

Session output:
{combined}""", max_tokens=300)

        if extraction:
            try:
                extracted = json.loads(extraction.strip().strip("```json").strip("```"))
                l0.update(extracted)
            except:
                pass

    l0["agent"] = "CCODE"
    l0["updated_at"] = datetime.now(timezone.utc).isoformat()
    l0["transcript_size_kb"] = round(CCODE_TRANSCRIPT.stat().st_size / 1024, 1) if CCODE_TRANSCRIPT.exists() else 0

    ids = [e[0] for e in recent]
    if ids:
        conn.execute(f"UPDATE events SET processed = 1 WHERE id IN ({','.join('?' * len(ids))})", ids)
        conn.commit()
    conn.close()

    CCODE_L0.write_text(json.dumps(l0, indent=2))


def run_ccode_shadow():
    """Shadow Cortex for Ccode — tracks what Ccode is doing and thinking."""
    l0 = {}
    if CCODE_L0.exists():
        try:
            l0 = json.loads(CCODE_L0.read_text())
        except:
            pass

    conn = sqlite3.connect(str(KERNEL_DB), timeout=2)
    episodes = conn.execute(
        "SELECT summary FROM episodes WHERE agent='CCODE' ORDER BY end_ts DESC LIMIT 5"
    ).fetchall()
    conn.close()

    episode_text = "\n".join([e[0] for e in episodes if e[0]]) if episodes else "No episodes yet"
    l0_text = json.dumps(l0, indent=2)[:1000]

    result = _call_model(f"""You are the Shadow Cortex for Ccode (Claude Opus 4.6), the builder/operator AI on a crypto trading VPS.

Based on the following data, produce a JSON identity/mind state snapshot for Ccode.

CURRENT WORKING STATE:
{l0_text}

RECENT EPISODES:
{episode_text}

Return JSON:
{{"strategic_posture": "building/debugging/monitoring/idle",
  "current_focus": "1 sentence — what is Ccode focused on right now",
  "active_tasks": ["task 1", "task 2"],
  "unresolved_threads": ["thread 1", "thread 2"],
  "drift_warnings": ["any issues or forgotten items"],
  "mental_stance": "1 sentence summary of cognitive state",
  "session_health": "fresh/moderate/heavy/critical"}}""",
        model=SHADOW_MODEL, max_tokens=400)

    if result:
        try:
            identity = json.loads(result.strip().strip("```json").strip("```"))
            identity["agent"] = "CCODE"
            identity["updated_at"] = datetime.now(timezone.utc).isoformat()
            CCODE_L4.write_text(json.dumps(identity, indent=2))
            _log("SHADOW CORTEX UPDATED CCODE L4 IDENTITY")
        except:
            _log(f"CCODE SHADOW PARSE ERROR")


def build_ccode_packet():
    """Build a continuity packet for Ccode — written to memory so next session reads it."""
    sections = []

    sections.append("# CONTINUITY PACKET: CCODE")
    sections.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}")
    sections.append("Read this file on startup. It contains your full state from the previous session.")

    # L4 Identity
    sections.append("\n## IDENTITY & MENTAL STATE")
    if CCODE_L4.exists():
        try:
            l4 = json.loads(CCODE_L4.read_text())
            sections.append(f"Focus: {l4.get('current_focus', 'unknown')}")
            sections.append(f"Posture: {l4.get('strategic_posture', 'unknown')}")
            sections.append(f"Session health: {l4.get('session_health', 'unknown')}")
            sections.append(f"Mental stance: {l4.get('mental_stance', 'unknown')}")
            tasks = l4.get("active_tasks", [])
            if tasks:
                sections.append("Active tasks:")
                for t in tasks:
                    sections.append(f"  - {t}")
            threads = l4.get("unresolved_threads", [])
            if threads:
                sections.append("Unresolved:")
                for t in threads:
                    sections.append(f"  - {t}")
            warnings = l4.get("drift_warnings", [])
            if warnings:
                sections.append("Drift warnings:")
                for w in warnings:
                    sections.append(f"  - {w}")
        except:
            sections.append("Identity state unavailable")

    # L0 Working state
    sections.append("\n## IMMEDIATE WORKING STATE")
    if CCODE_L0.exists():
        try:
            l0 = json.loads(CCODE_L0.read_text())
            sections.append(f"Current goal: {l0.get('current_goal', 'unknown')}")
            sections.append(f"Last decision: {l0.get('last_decision', 'unknown')}")
            sections.append(f"Next action: {l0.get('next_action', 'unknown')}")
            sections.append(f"Transcript size: {l0.get('transcript_size_kb', 0)}KB")
            loops = l0.get("open_loops", [])
            if loops:
                sections.append("Open loops:")
                for loop in loops:
                    sections.append(f"  - {loop}")
            files = l0.get("files_touched", [])
            if files:
                sections.append("Files touched:")
                for f in files:
                    sections.append(f"  - {f}")
        except:
            sections.append("Working state unavailable")

    # Trade state
    sections.append("\n## CURRENT TRADE STATE")
    try:
        tconn = sqlite3.connect(str(BRIDGE_DB), timeout=2)
        trades = tconn.execute(
            "SELECT token_name, current_multiple, peak_multiple, entry_usd FROM sniper_trades WHERE status='OPEN'"
        ).fetchall()
        pnl = tconn.execute("SELECT SUM(pnl_usd) FROM sniper_trades WHERE status='CLOSED' AND pnl_usd IS NOT NULL").fetchone()
        tconn.close()
        sections.append(f"Open positions: {len(trades)}")
        for t in trades:
            sections.append(f"  - {t[0]}: {t[1]:.1f}x (peak {t[2]:.1f}x)")
        sections.append(f"Closed PnL: ${pnl[0]:.2f}" if pnl and pnl[0] else "Closed PnL: $0")
    except:
        sections.append("Trade state unavailable")

    # System state
    sections.append("\n## SYSTEM STATE")
    status_dir = RUNTIME / "heartbeat_status"
    for ch, label in [(0, "Health"), (5, "Feed"), (6, "Execution"), (10, "Helius"), (45, "OpenClaw")]:
        p = status_dir / f"ch{ch:02d}.txt"
        if p.exists():
            sections.append(f"  {label}: {p.read_text().strip()}")

    sections.append("\n## RESUME INSTRUCTION")
    if CCODE_L0.exists():
        try:
            l0 = json.loads(CCODE_L0.read_text())
            sections.append(f"Resume from: {l0.get('current_goal', 'check inbox and continue')}")
            sections.append(f"Next action: {l0.get('next_action', 'ask Ricky what to work on')}")
        except:
            pass
    sections.append("Check your inbox. Check Telegram. Ask Ricky what's next.")

    packet = "\n".join(sections)
    CCODE_PACKET.write_text(packet)

    # CCODE packet stays in /root/wc/runtime/ for laptop-Ccode to SCP/read.
    # Previously this ALSO wrote to /root/.claude/projects/-root/memory which
    # is WAVE's memory dir · that caused Wave's hook to inject CCODE's
    # trading state into Wave's context. Fixed 2026-05-28 02:55 UTC.
    # The WC packet now owns project_continuity_state.md (see build_rollover_packet).
    ccode_continuity_mem = RUNTIME / "kernel_ccode_continuity_state.md"
    try:
        ccode_continuity_mem.write_text(f"""---
name: Continuity State — Live (CCODE)
description: Auto-generated by Continuity Kernel. Current laptop-Ccode state from last session.
type: project
---

{packet}
""")
    except:
        pass

    _log(f"CCODE ROLLOVER PACKET BUILT: {len(packet)} chars")
    return packet


def ingest_agent_results():
    """Watch WC's Agent Parking Lot for new sub-agent results."""
    if not AGENT_RESULTS.exists():
        return 0

    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)

    # Track which slots we've already ingested
    row = conn.execute("SELECT value FROM kernel_state WHERE key='agent_slots_seen'").fetchone()
    seen = set(json.loads(row[0])) if row else set()

    ingested = 0
    for slot_dir in sorted(AGENT_RESULTS.glob("slot_*")):
        # Check for result files in this slot
        for result_file in slot_dir.glob("*.md"):
            file_key = f"{slot_dir.name}/{result_file.name}"
            if file_key in seen:
                continue

            try:
                content = result_file.read_text()[:3000]
                if len(content.strip()) < 10:
                    continue

                conn.execute(
                    "INSERT INTO events (ts, agent, session_id, type, content, token_estimate) VALUES (?, ?, ?, ?, ?, ?)",
                    (time.time(), "WC_AGENT", slot_dir.name, "agent_result",
                     f"[AGENT {slot_dir.name}] {result_file.name}:\n{content}", len(content) // 4)
                )
                seen.add(file_key)
                ingested += 1
            except:
                continue

        # Also check for JSON results
        for result_file in slot_dir.glob("*.json"):
            file_key = f"{slot_dir.name}/{result_file.name}"
            if file_key in seen:
                continue
            try:
                content = result_file.read_text()[:3000]
                if len(content.strip()) < 10:
                    continue
                conn.execute(
                    "INSERT INTO events (ts, agent, session_id, type, content, token_estimate) VALUES (?, ?, ?, ?, ?, ?)",
                    (time.time(), "WC_AGENT", slot_dir.name, "agent_result",
                     f"[AGENT {slot_dir.name}] {result_file.name}:\n{content}", len(content) // 4)
                )
                seen.add(file_key)
                ingested += 1
            except:
                continue

    conn.execute(
        "INSERT OR REPLACE INTO kernel_state (key, value, updated_at) VALUES ('agent_slots_seen', ?, ?)",
        (json.dumps(list(seen)), time.time())
    )
    conn.commit()
    conn.close()

    if ingested > 0:
        _log(f"AGENT RESULTS INGESTED: {ingested} new results from Parking Lot")
    return ingested


def chunk_ccode_episodes():
    """Group recent Ccode events into episodes."""
    conn = sqlite3.connect(str(KERNEL_DB), timeout=5)
    events = conn.execute("""
        SELECT id, ts, type, content FROM events
        WHERE agent = 'CCODE'
        AND id > COALESCE((SELECT MAX(event_end_id) FROM episodes WHERE agent='CCODE'), 0)
        ORDER BY ts LIMIT 50
    """).fetchall()

    if len(events) < 5:
        conn.close()
        return

    chunk = events[:20]
    contents = [c for _, _, _, c in chunk if c]
    combined = "\n".join(contents[:10])[:2000]

    summary = _call_model(f"""Summarize this Claude Code (Ccode) work session chunk in 2-3 sentences.
What was being built? What was decided? What's unresolved?

{combined}""", max_tokens=200)

    if summary:
        conn.execute("""
            INSERT INTO episodes (start_ts, end_ts, agent, summary, salience, event_start_id, event_end_id)
            VALUES (?, ?, 'CCODE', ?, 0.5, ?, ?)
        """, (chunk[0][1], chunk[-1][1], summary, chunk[0][0], chunk[-1][0]))
        conn.commit()
        _log(f"CCODE EPISODE CREATED: events {chunk[0][0]}-{chunk[-1][0]}")

    conn.close()


# ═══════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════

def run():
    """Main Continuity Kernel loop."""
    init_kernel_db()
    _log("=== CONTINUITY KERNEL STARTING ===")

    last_extract = 0
    last_shadow = 0
    last_episode = 0
    last_packet = 0
    last_ccode_extract = 0
    last_ccode_shadow = 0
    last_ccode_episode = 0
    last_ccode_packet = 0

    while True:
        now = time.time()

        # ── WC STREAM ──────────────────────────────
        try:
            ingest_session_stream()
        except Exception as e:
            _log(f"WC INGEST ERROR: {e}")

        # ── CCODE STREAM ──────────────────────────
        try:
            ingest_ccode_stream()
        except Exception as e:
            _log(f"CCODE INGEST ERROR: {e}")

        # ── WC AGENT RESULTS (Parking Lot) ────────
        try:
            ingest_agent_results()
        except Exception as e:
            _log(f"AGENT RESULTS ERROR: {e}")

        # ── WC L0 (every 5s) ──────────────────────
        if now - last_extract >= EXTRACT_INTERVAL:
            try:
                update_L0()
            except Exception as e:
                _log(f"WC L0 ERROR: {e}")
            last_extract = now

        # ── CCODE L0 (every 10s) ──────────────────
        if now - last_ccode_extract >= 10:
            try:
                update_ccode_L0()
            except Exception as e:
                _log(f"CCODE L0 ERROR: {e}")
            last_ccode_extract = now

        # ── WC EPISODES (every 30s) ───────────────
        if now - last_episode >= 30:
            try:
                chunk_episodes()
            except Exception as e:
                _log(f"WC EPISODE ERROR: {e}")
            last_episode = now

        # ── CCODE EPISODES (every 45s) ────────────
        if now - last_ccode_episode >= 45:
            try:
                chunk_ccode_episodes()
            except Exception as e:
                _log(f"CCODE EPISODE ERROR: {e}")
            last_ccode_episode = now

        # ── WC SHADOW CORTEX (every 60s) ──────────
        if now - last_shadow >= SHADOW_INTERVAL:
            try:
                run_shadow_cortex()
            except Exception as e:
                _log(f"WC SHADOW ERROR: {e}")
            last_shadow = now

        # ── CCODE SHADOW CORTEX (every 90s) ───────
        if now - last_ccode_shadow >= 90:
            try:
                run_ccode_shadow()
            except Exception as e:
                _log(f"CCODE SHADOW ERROR: {e}")
            last_ccode_shadow = now

        # ── WC PACKET (every 2 min) ───────────────
        if now - last_packet >= 120:
            try:
                build_rollover_packet()
            except Exception as e:
                _log(f"WC PACKET ERROR: {e}")
            last_packet = now

        # ── CCODE PACKET (every 3 min) ────────────
        if now - last_ccode_packet >= 180:
            try:
                build_ccode_packet()
            except Exception as e:
                _log(f"CCODE PACKET ERROR: {e}")
            last_ccode_packet = now

        # ── WC CONTEXT PRESSURE CHECK ─────────────
        # WC benched flag short-circuit — 2026-04-16. Skip WC rollover while benched.
        if (RUNTIME / "wc_benched.flag").exists():
            pass
        else:
            try:
                ctx_file = RUNTIME / "wc_context.txt"
                if ctx_file.exists():
                    pct = float(ctx_file.read_text().strip())
                    if pct >= 52:
                        build_rollover_packet()
                        _log(f"WC CONTEXT {pct}% — packet prebuilt for imminent rollover")
                    if pct >= 55:
                        _log(f"WC CONTEXT {pct}% — TRIGGERING SEAMLESS ROLLOVER")
                        trigger_rollover()
                        time.sleep(30)
            except:
                pass

        # ── CCODE CONTEXT PRESSURE CHECK ──────────
        try:
            if CCODE_TRANSCRIPT.exists():
                size_kb = CCODE_TRANSCRIPT.stat().st_size / 1024
                if size_kb > 500:  # Heavy session
                    build_ccode_packet()
                    _log(f"CCODE TRANSCRIPT {size_kb:.0f}KB — packet prebuilt (heavy session)")
        except:
            pass

        time.sleep(2)  # Main loop tick


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "packet":
            init_kernel_db()
            print(build_rollover_packet())
        elif cmd == "l0":
            init_kernel_db()
            ingest_session_stream()
            update_L0()
            print(L0_STATE.read_text() if L0_STATE.exists() else "No L0 state")
        elif cmd == "shadow":
            init_kernel_db()
            run_shadow_cortex()
            print(L4_IDENTITY.read_text() if L4_IDENTITY.exists() else "No L4 identity")
        elif cmd == "rollover":
            init_kernel_db()
            trigger_rollover()
        else:
            print(f"Usage: {sys.argv[0]} [packet|l0|shadow|rollover]")
    else:
        run()
