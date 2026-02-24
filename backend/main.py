"""Business Signal Analyzer - FastAPI Backend"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from storage.database import (
    init_db, create_conversation, get_conversation, list_conversations,
    create_message, get_messages_by_conversation,
    create_topic, get_topics_by_conversation, update_topic_message_count,
    create_pain_point, get_pain_points_by_topic,
    create_demand_signal, get_demand_signals_by_topic, get_demand_signals_stats,
    create_business_idea, get_business_ideas, update_idea_score,
    create_evidence_link, get_evidence_by_idea
)
from connectors.google_trends import GoogleTrendsConnector
from connectors.reddit import RedditConnector
from connectors.hackernews import HackerNewsConnector
from connectors.youtube import YouTubeConnector
from scoring.engine import ScoringEngine

# Initialize
app = FastAPI(title="Business Signal Analyzer", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()
    print("✓ Database initialized")

# Initialize connectors (mock mode if no keys)
gtrends = GoogleTrendsConnector(mock_mode=True)
reddit = RedditConnector(mock_mode=True)
hn = HackerNewsConnector()
youtube = YouTubeConnector(mock_mode=True)

# Initialize scoring engine
weights_path = Path(__file__).parent / "scoring" / "weights.yaml"
scorer = ScoringEngine(weights_path)

# Pydantic models
class ConversationCreate(BaseModel):
    text: str
    source_type: str = "paste"

class TopicResponse(BaseModel):
    id: int
    name: str
    description: str
    message_count: int
    keywords: List[str]

class BusinessIdeaCreate(BaseModel):
    topic_id: int
    title: str
    target_user: str
    value_prop: str
    why_now: Optional[str] = None
    pricing_model: Optional[str] = None
    distribution_channel: Optional[str] = None
    moat: Optional[str] = None
    ops_burden_estimate: str = "medium"
    compliance_risks: Optional[str] = None

class ScoreWeights(BaseModel):
    demand_strength: float = 0.25
    demand_velocity: float = 0.20
    competition_proxy: float = 0.15
    feasibility: float = 0.20
    automation_friendly: float = 0.10
    monetization_clarity: float = 0.10

# Routes
@app.get("/")
async def root():
    return {
        "app": "Business Signal Analyzer",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/conversations",
            "/api/topics",
            "/api/demand",
            "/api/ideas",
            "/api/scoring/weights"
        ]
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Conversation endpoints
@app.post("/api/conversations")
async def create_conversation_endpoint(data: ConversationCreate):
    """Create a new conversation from text."""
    # Generate hash of text
    text_hash = hashlib.sha256(data.text.encode()).hexdigest()
    summary = data.text[:500]
    
    try:
        conv_id = create_conversation(data.source_type, text_hash, summary)
        
        # Simple message extraction (split by newlines or speakers)
        lines = data.text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # Try to detect speaker (simple heuristic)
                speaker = None
                if ':' in line[:50]:
                    parts = line.split(':', 1)
                    if len(parts) == 2 and len(parts[0]) < 30:
                        speaker = parts[0].strip()
                        line = parts[1].strip()
                
                create_message(conv_id, line, speaker)
        
        return {
            "id": conv_id,
            "message_count": len(lines),
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def list_conversations_endpoint(limit: int = 50):
    """List recent conversations."""
    return list_conversations(limit)

@app.get("/api/conversations/{conv_id}")
async def get_conversation_endpoint(conv_id: int):
    """Get conversation details."""
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = get_messages_by_conversation(conv_id)
    return {
        **conv,
        "messages": messages
    }

# Topic endpoints
@app.post("/api/topics")
async def create_topic_endpoint(
    conversation_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    keywords: str = Form("[]")
):
    """Create a new topic cluster."""
    try:
        kw_list = json.loads(keywords)
        topic_id = create_topic(conversation_id, name, description, kw_list)
        return {"id": topic_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/topics")
async def list_topics_endpoint(conversation_id: Optional[int] = None):
    """List topics, optionally filtered by conversation."""
    if conversation_id:
        return get_topics_by_conversation(conversation_id)
    return []  # TODO: add get_all_topics()

# Demand signal endpoints
@app.post("/api/demand/collect")
async def collect_demand_signals(topic_id: int, queries: List[str]):
    """Collect demand signals for a topic across all sources."""
    signals_collected = []
    
    for query in queries:
        # Google Trends
        for signal in gtrends.search(query):
            sid = create_demand_signal(
                topic_id, signal.source, signal.query,
                signal.metric_type, signal.metric_value,
                signal.metric_unit, signal.url
            )
            signals_collected.append({"id": sid, "source": signal.source})
        
        # Reddit
        for signal in reddit.search(query):
            sid = create_demand_signal(
                topic_id, signal.source, signal.query,
                signal.metric_type, signal.metric_value,
                signal.metric_unit, signal.url
            )
            signals_collected.append({"id": sid, "source": signal.source})
        
        # Hacker News
        for signal in hn.search(query):
            sid = create_demand_signal(
                topic_id, signal.source, signal.query,
                signal.metric_type, signal.metric_value,
                signal.metric_unit, signal.url
            )
            signals_collected.append({"id": sid, "source": signal.source})
        
        # YouTube
        for signal in youtube.search(query):
            sid = create_demand_signal(
                topic_id, signal.source, signal.query,
                signal.metric_type, signal.metric_value,
                signal.metric_unit, signal.url
            )
            signals_collected.append({"id": sid, "source": signal.source})
    
    return {
        "topic_id": topic_id,
        "signals_collected": len(signals_collected),
        "sources": list(set(s["source"] for s in signals_collected))
    }

@app.get("/api/demand/topic/{topic_id}")
async def get_demand_for_topic(topic_id: int):
    """Get all demand signals for a topic."""
    signals = get_demand_signals_by_topic(topic_id)
    stats = get_demand_signals_stats(topic_id)
    
    return {
        "signals": signals,
        "stats": stats
    }

# Business idea endpoints
@app.post("/api/ideas")
async def create_idea_endpoint(idea: BusinessIdeaCreate):
    """Create a new business idea."""
    try:
        idea_id = create_business_idea(
            topic_id=idea.topic_id,
            title=idea.title,
            target_user=idea.target_user,
            value_prop=idea.value_prop,
            why_now=idea.why_now,
            pricing_model=idea.pricing_model,
            distribution_channel=idea.distribution_channel,
            moat=idea.moat,
            ops_burden_estimate=idea.ops_burden_estimate,
            compliance_risks=idea.compliance_risks
        )
        return {"id": idea_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ideas")
async def list_ideas_endpoint(topic_id: Optional[int] = None, min_score: float = 0.0):
    """List business ideas with scores."""
    return get_business_ideas(topic_id, min_score)

@app.post("/api/ideas/{idea_id}/score")
async def score_idea_endpoint(idea_id: int):
    """Recalculate score for a business idea."""
    # Get idea
    ideas = get_business_ideas(min_score=0.0)
    idea = next((i for i in ideas if i['id'] == idea_id), None)
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Get signals for topic
    signals = get_demand_signals_by_topic(idea['topic_id'])
    
    # Calculate score
    breakdown = scorer.score_idea(idea, signals)
    
    # Update database
    update_idea_score(idea_id, breakdown.total, json.dumps(breakdown.to_dict()))
    
    return breakdown.to_dict()

@app.post("/api/ideas/rank")
async def rank_ideas_endpoint(topic_id: int):
    """Rank all ideas for a topic."""
    # Get all ideas for topic
    ideas = get_business_ideas(topic_id, min_score=0.0)
    
    # Pair with signals and rank
    ideas_with_signals = []
    for idea in ideas:
        signals = get_demand_signals_by_topic(idea['topic_id'])
        ideas_with_signals.append((idea, signals))
    
    ranked = scorer.rank_ideas(ideas_with_signals)
    
    # Update ranks in database
    for idea in ranked:
        update_idea_score(
            idea['id'], 
            idea['total_score'], 
            json.dumps(idea['score_breakdown'])
        )
    
    return ranked

# Evidence endpoints
@app.post("/api/evidence")
async def add_evidence(
    idea_id: int = Form(...),
    url: str = Form(...),
    title: str = Form(""),
    snippet: str = Form(""),
    source: str = Form(""),
    relevance_score: float = Form(0.5)
):
    """Add evidence link to a business idea."""
    try:
        link_id = create_evidence_link(
            idea_id, url, title, snippet, source, relevance_score
        )
        return {"id": link_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evidence/idea/{idea_id}")
async def get_evidence_for_idea(idea_id: int, limit: int = 10):
    """Get evidence links for a business idea."""
    return get_evidence_by_idea(idea_id, limit)

# Scoring config endpoints
@app.get("/api/scoring/weights")
async def get_scoring_weights():
    """Get current scoring weights configuration."""
    return scorer.get_weights_config()

@app.post("/api/scoring/weights")
async def update_scoring_weights(weights: ScoreWeights):
    """Update scoring weights (creates new engine instance)."""
    global scorer
    
    new_weights = {
        'demand_strength': weights.demand_strength,
        'demand_velocity': weights.demand_velocity,
        'competition_proxy': weights.competition_proxy,
        'feasibility': weights.feasibility,
        'automation_friendly': weights.automation_friendly,
        'monetization_clarity': weights.monetization_clarity
    }
    
    # Validate weights sum to ~1.0
    total = sum(new_weights.values())
    if abs(total - 1.0) > 0.01:
        # Normalize
        new_weights = {k: v/total for k, v in new_weights.items()}
    
    # Update weights file
    weights_path = Path(__file__).parent / "scoring" / "weights.yaml"
    with open(weights_path, 'w') as f:
        yaml.dump({'weights': new_weights}, f)
    
    # Recreate scorer with new weights
    scorer = ScoringEngine(weights_path)
    
    return {"status": "updated", "weights": new_weights}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
