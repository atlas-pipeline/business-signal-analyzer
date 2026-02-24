CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_type TEXT NOT NULL, -- 'paste', 'upload', 'telegram'
    raw_text_hash TEXT UNIQUE, -- SHA256 of raw input
    raw_summary TEXT -- First 500 chars for display
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    speaker TEXT, -- 'user', 'assistant', or null
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    message_count INTEGER DEFAULT 0,
    keywords TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS pain_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    statement TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    severity_score REAL DEFAULT 0.5, -- 0.0 to 1.0
    evidence_quote TEXT,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

CREATE TABLE IF NOT EXISTS demand_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    source TEXT NOT NULL, -- 'google_trends', 'reddit', 'hackernews', 'youtube'
    query TEXT NOT NULL,
    metric_type TEXT NOT NULL, -- 'volume', 'growth_rate', 'engagement', 'count'
    metric_value REAL,
    metric_unit TEXT,
    url TEXT NOT NULL, -- Source URL
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_date DATE, -- When the data was collected
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

CREATE TABLE IF NOT EXISTS business_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    target_user TEXT NOT NULL,
    value_prop TEXT NOT NULL,
    why_now TEXT,
    pricing_model TEXT,
    distribution_channel TEXT,
    moat TEXT,
    ops_burden_estimate TEXT, -- 'low', 'medium', 'high'
    compliance_risks TEXT,
    total_score REAL DEFAULT 0.0,
    score_breakdown TEXT, -- JSON
    rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

CREATE TABLE IF NOT EXISTS evidence_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    snippet TEXT,
    source TEXT NOT NULL,
    relevance_score REAL DEFAULT 0.5,
    FOREIGN KEY (idea_id) REFERENCES business_ideas(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_topics_conversation ON topics(conversation_id);
CREATE INDEX IF NOT EXISTS idx_pain_points_topic ON pain_points(topic_id);
CREATE INDEX IF NOT EXISTS idx_demand_signals_topic ON demand_signals(topic_id);
CREATE INDEX IF NOT EXISTS idx_demand_signals_source ON demand_signals(source, query);
CREATE INDEX IF NOT EXISTS idx_business_ideas_topic ON business_ideas(topic_id);
CREATE INDEX IF NOT EXISTS idx_evidence_idea ON evidence_links(idea_id);
