# Business Signal Analyzer

Turn conversation notes and public demand signals into ranked business ideas with evidence.

## What It Does

1. **Ingest** - Paste customer conversations or upload text files
2. **Extract** - Automatically identify topic clusters and pain points
3. **Collect** - Gather demand signals from Google Trends, Reddit, Hacker News, YouTube
4. **Generate** - Create business ideas mapped to pain points
5. **Score** - Rank ideas with transparent weighted model
6. **Evidence** - Every claim backed by traceable source URLs

## Quick Start (Local)

### Prerequisites
- Python 3.8+
- (Optional) API keys for Reddit and YouTube (see below)

### 1. Clone/Navigate to Project
```bash
cd business-signal-analyzer
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Configure API Keys (Optional)
```bash
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

**Without API keys:** The app runs in "mock mode" with synthetic data for testing.

**With API keys:** You get live data from all sources.

### 5. Initialize Database
```bash
cd backend
python -c "from storage.database import init_db; init_db()"
```

### 6. Start Backend Server
```bash
python main.py
```

Server starts at `http://localhost:8000`

### 7. Open Frontend
Open `frontend/index.html` in your browser (or use Live Server extension).

## API Documentation

Once running, view interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:
```bash
cd tests
pytest -v
```

## Deployment

### Option 1: Render (Recommended)

1. Push code to GitHub
2. Go to [dashboard.render.com](https://dashboard.render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Set build command: `pip install -r backend/requirements.txt`
6. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add environment variables from `config/.env`

### Option 2: Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Option 3: VPS/Dedicated Server

```bash
# On your server
git clone <your-repo>
cd business-signal-analyzer
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Run with gunicorn
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Architecture

```
business-signal-analyzer/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── api/                 # Route handlers
│   ├── connectors/          # Data source adapters
│   │   ├── google_trends.py
│   │   ├── reddit.py
│   │   ├── hackernews.py
│   │   └── youtube.py
│   ├── scoring/             # Scoring engine
│   │   ├── engine.py
│   │   └── weights.yaml
│   ├── storage/             # Database
│   │   ├── database.py
│   │   └── migrations.sql
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Ingest UI
│   ├── topics.html          # Topics list
│   ├── ideas.html           # Ranked ideas
│   └── evidence.html        # Evidence report
├── tests/
│   ├── test_connectors.py
│   └── test_scoring.py
└── config/
    └── .env.example
```

## Data Sources

| Source | Method | API Key Required | Notes |
|--------|--------|------------------|-------|
| Google Trends | pytrends | No | Rate limited |
| Reddit | PRAW (Official) | Yes | 60 requests/min |
| Hacker News | Firebase API | No | Public, generous limits |
| YouTube | Data API v3 | Yes | 10,000 quota units/day |

## Scoring Model

Ideas are scored 0-100 on six dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Demand Strength | 25% | Volume of mentions/signals |
| Demand Velocity | 20% | Growth trend / recency |
| Competition Proxy | 15% | Market saturation (inverse) |
| Feasibility | 20% | Build complexity and risk |
| Automation Friendly | 10% | Low oversight potential |
| Monetization Clarity | 10% | Clear pricing + buyer |

Weights are configurable in `backend/scoring/weights.yaml`.

## Ethical & Legal Compliance

- ✅ Respects robots.txt (where applicable)
- ✅ Uses official APIs only
- ✅ No CAPTCHA bypass
- ✅ No login/authentication bypass
- ✅ Rate limiting on all requests
- ✅ Respects Terms of Service

## Roadmap / Stubbed Features

**Implemented in MVP:**
- ✅ Basic conversation ingestion
- ✅ Topic extraction (manual)
- ✅ Demand signal collection (4 sources)
- ✅ Business idea creation
- ✅ Transparent scoring
- ✅ Evidence tracking

**Next Enhancements:**
- [ ] Auto topic extraction with NLP
- [ ] Pain point auto-detection
- [ ] More data sources (Twitter/X, LinkedIn)
- [ ] Idea generation with LLM
- [ ] Export to PDF/Notion
- [ ] Scheduled monitoring (alerts when demand spikes)
- [ ] A/B test tracking for ideas

## License

MIT

## Support

For issues or questions, check:
1. API docs at `/docs` when running locally
2. Test suite: `pytest tests/ -v`
3. Logs in backend console
