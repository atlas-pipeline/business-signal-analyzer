# Business Signal Analyzer - Product Spec

## Overview
A local web app that transforms conversation notes + public demand signals into ranked, evidence-backed business ideas.

## Architecture
- **Backend**: Python FastAPI + SQLite
- **Frontend**: Plain HTML + vanilla JS (minimal, maintainable)
- **Connectors**: Adapter pattern for each data source
- **Scoring**: Transparent weighted model with config

## Folder Structure
```
business-signal-analyzer/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   ├── ingestion.py     # Conversation upload endpoints
│   │   ├── topics.py        # Topic cluster endpoints
│   │   ├── demand.py        # Demand signal endpoints
│   │   └── ideas.py         # Business idea endpoints
│   ├── connectors/
│   │   ├── base.py          # Abstract base class
│   │   ├── google_trends.py
│   │   ├── reddit.py
│   │   ├── hackernews.py
│   │   └── youtube.py       # Optional
│   ├── scoring/
│   │   ├── weights.yaml     # Configurable weights
│   │   └── engine.py        # Scoring computation
│   ├── storage/
│   │   ├── database.py      # SQLite connection
│   │   └── migrations.sql   # Schema
│   └── pipeline/
│       ├── extractor.py     # Pain point extraction
│       └── clusterer.py     # Topic clustering
├── frontend/
│   ├── index.html           # Dashboard
│   ├── ingest.html          # Upload/paste UI
│   ├── topics.html          # Topic clusters
│   ├── ideas.html           # Ranked ideas
│   └── evidence.html        # Evidence report
├── config/
│   └── .env.example
├── docs/
│   └── README.md
└── tests/
    ├── test_connectors.py
    └── test_scoring.py
```

## Core Data Model

### conversations
- id, created_at, source_type, raw_text_hash

### messages (extracted)
- id, conversation_id, text, speaker, timestamp

### topics (clustered)
- id, name, description, message_count, embedding_vector

### pain_points
- id, topic_id, statement, frequency, severity_score

### demand_signals
- id, topic_id, source, query, metric_type, value, url, timestamp

### business_ideas
- id, topic_id, title, target_user, value_prop, pricing_model, score, score_breakdown

### evidence_links
- id, idea_id, url, title, snippet, relevance_score

## Scoring Weights (configurable)
```yaml
weights:
  demand_strength: 0.25      # Volume of mentions
  demand_velocity: 0.20      # Trend slope / recency
  competition_proxy: 0.15    # Saturation estimate
  feasibility: 0.20          # Build complexity
  automation_friendly: 0.10  # Low oversight potential
  monetization_clarity: 0.10 # Clear pricing + buyer
```

## API Keys Required
- Reddit: https://www.reddit.com/prefs/apps
- YouTube: https://console.cloud.google.com/apis/credentials
- Google Trends: None (uses pytrends, rate-limited)
- Hacker News: None (Firebase API is public)

## Mock Mode
All connectors work in "mock mode" without keys, returning synthetic data for testing.
