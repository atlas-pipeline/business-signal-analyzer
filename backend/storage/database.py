"""Database connection and operations."""
import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Database path
DB_PATH = Path(__file__).parent / "data.db"

def init_db():
    """Initialize database with migrations."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    migrations_path = Path(__file__).parent / "migrations.sql"
    with open(migrations_path, "r") as f:
        migrations = f.read()
    
    with get_db() as db:
        db.executescript(migrations)
        db.commit()
    
    print(f"✓ Database initialized at {DB_PATH}")

@contextmanager
def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Conversation operations
def create_conversation(source_type: str, raw_text_hash: str, raw_summary: str) -> int:
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO conversations (source_type, raw_text_hash, raw_summary)
               VALUES (?, ?, ?)""",
            (source_type, raw_text_hash, raw_summary)
        )
        db.commit()
        return cursor.lastrowid

def get_conversation(conv_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conv_id,)
        ).fetchone()
        return dict(row) if row else None

def list_conversations(limit: int = 50) -> List[Dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM conversations ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

# Message operations
def create_message(conversation_id: int, text: str, speaker: Optional[str] = None) -> int:
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO messages (conversation_id, text, speaker)
               VALUES (?, ?, ?)""",
            (conversation_id, text, speaker)
        )
        db.commit()
        return cursor.lastrowid

def get_messages_by_conversation(conv_id: int) -> List[Dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (conv_id,)
        ).fetchall()
        return [dict(row) for row in rows]

# Topic operations
def create_topic(conversation_id: int, name: str, description: str = "", 
                 keywords: Optional[List[str]] = None) -> int:
    import json
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO topics (conversation_id, name, description, keywords)
               VALUES (?, ?, ?, ?)""",
            (conversation_id, name, description, json.dumps(keywords or []))
        )
        db.commit()
        return cursor.lastrowid

def get_topics_by_conversation(conv_id: int) -> List[Dict[str, Any]]:
    import json
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM topics WHERE conversation_id = ? ORDER BY message_count DESC",
            (conv_id,)
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d['keywords'] = json.loads(d.get('keywords', '[]'))
            result.append(d)
        return result

def update_topic_message_count(topic_id: int, count: int):
    with get_db() as db:
        db.execute(
            "UPDATE topics SET message_count = ? WHERE id = ?",
            (count, topic_id)
        )
        db.commit()

# Pain point operations
def create_pain_point(topic_id: int, statement: str, severity_score: float = 0.5,
                      evidence_quote: str = "") -> int:
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO pain_points (topic_id, statement, severity_score, evidence_quote)
               VALUES (?, ?, ?, ?)""",
            (topic_id, statement, severity_score, evidence_quote)
        )
        db.commit()
        return cursor.lastrowid

def get_pain_points_by_topic(topic_id: int) -> List[Dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            """SELECT * FROM pain_points 
               WHERE topic_id = ? 
               ORDER BY severity_score DESC, frequency DESC""",
            (topic_id,)
        ).fetchall()
        return [dict(row) for row in rows]

# Demand signal operations
def create_demand_signal(topic_id: int, source: str, query: str, 
                        metric_type: str, metric_value: float,
                        metric_unit: str, url: str) -> int:
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO demand_signals 
               (topic_id, source, query, metric_type, metric_value, metric_unit, url)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (topic_id, source, query, metric_type, metric_value, metric_unit, url)
        )
        db.commit()
        return cursor.lastrowid

def get_demand_signals_by_topic(topic_id: int) -> List[Dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM demand_signals WHERE topic_id = ? ORDER BY timestamp DESC",
            (topic_id,)
        ).fetchall()
        return [dict(row) for row in rows]

def get_demand_signals_stats(topic_id: int) -> Dict[str, Any]:
    """Get aggregated stats for demand signals on a topic."""
    with get_db() as db:
        row = db.execute(
            """SELECT 
                COUNT(*) as total_signals,
                COUNT(DISTINCT source) as sources,
                AVG(metric_value) as avg_value,
                MAX(timestamp) as latest_signal
               FROM demand_signals 
               WHERE topic_id = ?""",
            (topic_id,)
        ).fetchone()
        return dict(row) if row else {}

# Business idea operations
def create_business_idea(topic_id: int, title: str, target_user: str, 
                        value_prop: str, **kwargs) -> int:
    fields = ['topic_id', 'title', 'target_user', 'value_prop']
    values = [topic_id, title, target_user, value_prop]
    
    optional_fields = ['why_now', 'pricing_model', 'distribution_channel', 
                       'moat', 'ops_burden_estimate', 'compliance_risks',
                       'total_score', 'score_breakdown', 'rank']
    
    for field in optional_fields:
        if field in kwargs and kwargs[field] is not None:
            fields.append(field)
            values.append(kwargs[field])
    
    placeholders = ', '.join(['?' for _ in values])
    field_names = ', '.join(fields)
    
    with get_db() as db:
        cursor = db.execute(
            f"INSERT INTO business_ideas ({field_names}) VALUES ({placeholders})",
            values
        )
        db.commit()
        return cursor.lastrowid

def get_business_ideas(topic_id: Optional[int] = None, 
                       min_score: float = 0.0) -> List[Dict[str, Any]]:
    import json
    query = "SELECT * FROM business_ideas WHERE total_score >= ?"
    params = [min_score]
    
    if topic_id:
        query += " AND topic_id = ?"
        params.append(topic_id)
    
    query += " ORDER BY total_score DESC, rank ASC"
    
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get('score_breakdown'):
                d['score_breakdown'] = json.loads(d['score_breakdown'])
            result.append(d)
        return result

def update_idea_score(idea_id: int, total_score: float, score_breakdown: str):
    with get_db() as db:
        db.execute(
            """UPDATE business_ideas 
               SET total_score = ?, score_breakdown = ? 
               WHERE id = ?""",
            (total_score, score_breakdown, idea_id)
        )
        db.commit()

# Evidence link operations
def create_evidence_link(idea_id: int, url: str, title: str = "", 
                        snippet: str = "", source: str = "", 
                        relevance_score: float = 0.5) -> int:
    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO evidence_links 
               (idea_id, url, title, snippet, source, relevance_score)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (idea_id, url, title, snippet, source, relevance_score)
        )
        db.commit()
        return cursor.lastrowid

def get_evidence_by_idea(idea_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            """SELECT * FROM evidence_links 
               WHERE idea_id = ? 
               ORDER BY relevance_score DESC 
               LIMIT ?""",
            (idea_id, limit)
        ).fetchall()
        return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
