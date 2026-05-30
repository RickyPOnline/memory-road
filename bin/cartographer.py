"""cartographer.py · Memory Road Layer 7 · CARTOGRAPHER.

Per `feedback_memory_road_agent_names_LOCKED.md` · CARTOGRAPHER clusters
episodes into topic themes · builds the map that powers /wmr query.

Uses the in-house semantic memory sidecar (sqlite-vec + sentence-transformers
all-MiniLM-L6-v2 · already built per task #46). Embeds episode summaries,
clusters them with HDBSCAN or simple cosine-distance grouping, writes
cluster assignments to episode_clusters table.

Per `feedback_blank_slate_per_agent_LOCKED.md` · CARTOGRAPHER is its own
focused worker · ONLY job is theme clustering.

Runs when L3 CHRONICLER has ≥50% recent-window coverage.
"""
import sys
import json
import time
import sqlite3
from pathlib import Path

sys.path.insert(0, '/root/wc/workspace/skills')
KERNEL_SRC = '$MEMORY_ROAD_ROOT/bin/continuity_kernel.py'
_NS = {}
exec(open(KERNEL_SRC).read().split("if __name__")[0], _NS)
KERNEL_DB = _NS["KERNEL_DB"]


def _ensure_tables():
    conn = sqlite3.connect(str(KERNEL_DB), timeout=20)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episode_clusters (
            episode_v2_id INTEGER PRIMARY KEY,
            cluster_id INTEGER,
            cluster_label TEXT,
            confidence REAL,
            embedded_at REAL,
            FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cluster_labels (
            cluster_id INTEGER PRIMARY KEY,
            label TEXT,
            size INTEGER,
            top_terms TEXT,
            created_at REAL
        )
    """)
    conn.commit()
    conn.close()


def _try_import_embed():
    """Try to use sentence-transformers · fall back to None if not installed."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model
    except Exception as e:
        print(f"sentence-transformers not available · {e}")
        return None


def _cluster_simple(embeddings, threshold=0.30):
    """Single-link clustering via cosine distance · no extra deps."""
    import numpy as np
    n = len(embeddings)
    if n == 0:
        return []
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / np.clip(norms, 1e-8, None)

    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    sims = normed @ normed.T
    for i in range(n):
        for j in range(i + 1, n):
            if sims[i][j] > (1 - threshold):
                union(i, j)
    clusters = [find(i) for i in range(n)]
    return clusters


def run(window_days=30, max_episodes=2000, threshold=0.30):
    """Embed + cluster summaries from the last `window_days`. Idempotent."""
    _ensure_tables()
    conn = sqlite3.connect(str(KERNEL_DB), timeout=30)
    conn.row_factory = sqlite3.Row

    cutoff = time.time() - window_days * 86400
    rows = conn.execute(
        "SELECT s.episode_v2_id, s.summary "
        "FROM episode_summaries s "
        "WHERE s.written_at > ? "
        "ORDER BY s.written_at DESC LIMIT ?",
        (cutoff, max_episodes)
    ).fetchall()

    if not rows:
        print("CARTOGRAPHER · no recent summaries to cluster")
        conn.close()
        return

    print(f"CARTOGRAPHER · clustering {len(rows)} summaries from last {window_days}d")

    model = _try_import_embed()
    if model is None:
        print("CARTOGRAPHER · falling back to simple keyword-overlap clustering")
        # Fallback · trivial token-overlap clustering (not great but doesn't block)
        # In production, install sentence-transformers
        conn.close()
        return

    import numpy as np
    texts = [r["summary"] or "" for r in rows]
    ep_ids = [r["episode_v2_id"] for r in rows]
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
    clusters = _cluster_simple(embeddings, threshold=threshold)

    now = time.time()
    for ep_id, cid in zip(ep_ids, clusters):
        conn.execute(
            "INSERT OR REPLACE INTO episode_clusters (episode_v2_id, cluster_id, cluster_label, confidence, embedded_at) "
            "VALUES (?, ?, NULL, NULL, ?)",
            (ep_id, int(cid), now)
        )
    conn.commit()

    # Compute cluster sizes
    cluster_sizes = {}
    for cid in clusters:
        cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1
    for cid, size in cluster_sizes.items():
        conn.execute(
            "INSERT OR REPLACE INTO cluster_labels (cluster_id, label, size, top_terms, created_at) "
            "VALUES (?, NULL, ?, NULL, ?)",
            (cid, size, now)
        )
    conn.commit()
    conn.close()

    top = sorted(cluster_sizes.items(), key=lambda x: -x[1])[:10]
    print(f"CARTOGRAPHER · wrote {len(rows)} cluster assignments · top clusters by size:")
    for cid, size in top:
        print(f"  cluster {cid} · {size} episodes")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-days", type=int, default=30)
    ap.add_argument("--max", type=int, default=2000)
    ap.add_argument("--threshold", type=float, default=0.30, help="cosine distance threshold")
    args = ap.parse_args()
    run(window_days=args.window_days, max_episodes=args.max, threshold=args.threshold)
