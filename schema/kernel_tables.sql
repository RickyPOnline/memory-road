-- Memory Road · Kernel Schema · v1.0 · 2026-05-30
--
-- All tables Memory Road creates + uses. Idempotent · safe to re-run.
-- The kernel auto-creates these on first event ingest if they don't exist ·
-- but you can pre-create them with this file for a clean install.

-- =================================================================
-- L0 SUBSTRATE TABLES (always-on · LLM-free · sacred)
-- =================================================================

-- Raw events (every Claude Code transcript event lands here · forever)
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
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);

-- L1 FURROW · episodes (chunks of related consecutive events)
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
);
CREATE INDEX IF NOT EXISTS idx_episodes_v2_end ON episodes_v2(event_end_id);
CREATE INDEX IF NOT EXISTS idx_episodes_v2_agent ON episodes_v2(agent);

-- Kernel state (offsets · watermarks · active session pointer)
CREATE TABLE IF NOT EXISTS kernel_state (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- =================================================================
-- L3 CHRONICLER TABLES (snow plow summaries)
-- =================================================================

CREATE TABLE IF NOT EXISTS episode_summaries (
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
CREATE INDEX IF NOT EXISTS idx_summaries_eid ON episode_summaries(episode_v2_id);
CREATE INDEX IF NOT EXISTS idx_summaries_written_at ON episode_summaries(written_at);
CREATE INDEX IF NOT EXISTS idx_summaries_writer ON episode_summaries(writer_model);

-- L4 inspection (optional deeper analysis)
CREATE TABLE IF NOT EXISTS episode_inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_v2_id INTEGER NOT NULL,
    inspector_model TEXT NOT NULL,
    insights TEXT,
    written_at REAL NOT NULL,
    FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
);

-- =================================================================
-- L7 CARTOGRAPHER (topic clusters)
-- =================================================================

CREATE TABLE IF NOT EXISTS episode_clusters (
    episode_v2_id INTEGER PRIMARY KEY,
    cluster_id INTEGER,
    cluster_label TEXT,
    confidence REAL,
    embedded_at REAL,
    FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
);
CREATE INDEX IF NOT EXISTS idx_clusters_cid ON episode_clusters(cluster_id);

CREATE TABLE IF NOT EXISTS cluster_labels (
    cluster_id INTEGER PRIMARY KEY,
    label TEXT,
    size INTEGER,
    top_terms TEXT,
    created_at REAL
);

-- =================================================================
-- L6 MINER + SMITH (doctrine extraction)
-- =================================================================

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
);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidate_doctrines(status);

-- =================================================================
-- L12 HUNTSMAN (unfinished item flagger)
-- =================================================================

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
);
CREATE INDEX IF NOT EXISTS idx_huntsman_status ON huntsman_flags(status);
CREATE INDEX IF NOT EXISTS idx_huntsman_source ON huntsman_flags(source);

-- =================================================================
-- KERNEL UTILITY TABLES (open loops · facts · refinements)
-- =================================================================

CREATE TABLE IF NOT EXISTS open_loops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    opened_at REAL,
    still_open INTEGER DEFAULT 1,
    closed_at REAL,
    closure_reason TEXT
);

CREATE TABLE IF NOT EXISTS semantic_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL,
    subject TEXT,
    confidence REAL,
    source_episode_id INTEGER,
    created_at REAL,
    FOREIGN KEY (source_episode_id) REFERENCES episodes_v2(id)
);
CREATE INDEX IF NOT EXISTS idx_facts_subject ON semantic_facts(subject);

CREATE TABLE IF NOT EXISTS fact_refinements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_fact_id INTEGER,
    refined_fact TEXT,
    refiner_model TEXT,
    refined_at REAL,
    FOREIGN KEY (original_fact_id) REFERENCES semantic_facts(id)
);

CREATE TABLE IF NOT EXISTS episode_salience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_v2_id INTEGER NOT NULL,
    salience_score REAL,
    scored_by TEXT,
    scored_at REAL,
    FOREIGN KEY (episode_v2_id) REFERENCES episodes_v2(id)
);
