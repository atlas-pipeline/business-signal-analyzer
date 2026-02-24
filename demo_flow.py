"""
DEMO FLOW: Business Signal Analyzer
====================================

This script demonstrates the complete workflow from conversation to ranked ideas.
Run this after starting the backend server.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api"

def demo():
    print("=" * 60)
    print("BUSINESS SIGNAL ANALYZER - DEMO FLOW")
    print("=" * 60)
    
    # Step 1: Ingest conversation
    print("\n📥 Step 1: Ingesting conversation...")
    conversation = """
User: I run a small construction company in Calgary. Every week I spend 3-4 hours just chasing subcontractors for their WCB and insurance documents. It's a nightmare.

Me: What happens when they don't provide them on time?

User: Projects get delayed, clients get angry, and sometimes I have to pay rush fees to get alternate subs. Last month I lost a $50K project because I couldn't prove compliance fast enough.

Me: Do you have a system for tracking this?

User: Just spreadsheets and email folders. I have to manually check expiration dates and send reminder emails. It's error-prone - last year I missed a COR renewal and got fined.

Me: Would you pay for a service that automated this?

User: Absolutely. I'd pay $200-300/month easily if it saved me 10 hours a month and prevented delays. The fine alone was $5,000, so it pays for itself.

Me: What about your competitors?

User: They all have the same problem. I was talking to a guy at the Alberta Construction Association meeting - he said compliance paperwork is the #1 administrative headache for small GCs.
"""
    
    response = requests.post(f"{API_BASE}/conversations", json={
        "text": conversation,
        "source_type": "user_interview"
    })
    
    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return
    
    conv_data = response.json()
    conv_id = conv_data["id"]
    print(f"✅ Created conversation #{conv_id} with {conv_data['message_count']} messages")
    
    # Step 2: Create topics
    print("\n🏷️  Step 2: Creating topics...")
    
    topics = [
        {
            "conversation_id": conv_id,
            "name": "Subcontractor Compliance",
            "description": "Managing WCB, insurance, and COR documentation for subcontractors",
            "keywords": ["compliance", "WCB", "insurance", "subcontractor", "documentation"]
        },
        {
            "conversation_id": conv_id,
            "name": "Project Delays",
            "description": "Delays caused by administrative bottlenecks and missing paperwork",
            "keywords": ["delay", "project", "administrative", "paperwork", "bottleneck"]
        },
        {
            "conversation_id": conv_id,
            "name": "Spreadsheet Pain",
            "description": "Manual tracking in spreadsheets is error-prone and time-consuming",
            "keywords": ["spreadsheet", "manual", "tracking", "error", "time"]
        }
    ]
    
    topic_ids = []
    for topic in topics:
        response = requests.post(f"{API_BASE}/topics", data=topic)
        if response.status_code == 200:
            topic_id = response.json()["id"]
            topic_ids.append(topic_id)
            print(f"  ✅ Topic: {topic['name']} (ID: {topic_id})")
    
    # Step 3: Collect demand signals
    print("\n📊 Step 3: Collecting demand signals...")
    
    for topic_id in topic_ids[:2]:  # First 2 topics
        queries = ["construction compliance software", "subcontractor management", "WCB tracking"]
        response = requests.post(
            f"{API_BASE}/demand/collect",
            json={"topic_id": topic_id, "queries": queries}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Topic {topic_id}: {data['signals_collected']} signals from {', '.join(data['sources'])}")
    
    # Step 4: Create business ideas
    print("\n💡 Step 4: Creating business ideas...")
    
    ideas = [
        {
            "topic_id": topic_ids[0],
            "title": "SubContractor Pro - Automated Compliance Tracking",
            "target_user": "Small-to-mid general contractors ($2M-$10M revenue)",
            "value_prop": "Eliminate 10+ hours/week of paperwork chasing with automated compliance tracking",
            "why_now": "Alberta construction boom + increasing regulatory scrutiny",
            "pricing_model": "$149/mo Starter, $349/mo Growth, $799/mo Enterprise",
            "distribution_channel": "LinkedIn outreach + Alberta Construction Association",
            "moat": "Alberta-specific integrations (WCB Alberta, local insurers)",
            "ops_burden_estimate": "low",
            "compliance_risks": None
        },
        {
            "topic_id": topic_ids[0],
            "title": "ComplianceFile.ai - Smart Document Collection",
            "target_user": "Property managers and facility operators",
            "value_prop": "AI-powered document collection and verification for vendor compliance",
            "why_now": "Remote work increased vendor management complexity",
            "pricing_model": "$99/mo per property, $799/mo unlimited",
            "distribution_channel": "Property management software partnerships",
            "moat": "AI document classification, integrations with 50+ property systems",
            "ops_burden_estimate": "medium",
            "compliance_risks": "Data privacy regulations (PIPEDA)"
        },
        {
            "topic_id": topic_ids[1],
            "title": "ProjectPulse - Delay Prevention System",
            "target_user": "Construction project managers",
            "value_prop": "Predict and prevent project delays before they happen",
            "why_now": "Construction margins tight, delay costs increasing",
            "pricing_model": "$199/mo per active project",
            "distribution_channel": "Construction management software marketplaces",
            "moat": "Predictive analytics, integration with scheduling tools",
            "ops_burden_estimate": "high",
            "compliance_risks": "Professional liability if predictions are wrong"
        },
        {
            "topic_id": topic_ids[2],
            "title": "SheetSync - Spreadsheet Automation for Trades",
            "target_user": "Small trade contractors (electrical, plumbing, HVAC)",
            "value_prop": "Turn messy spreadsheets into automated workflows",
            "why_now": "Trades increasingly adopting digital tools post-COVID",
            "pricing_model": "$49/mo, $399/year",
            "distribution_channel": "Trade association newsletters, supply house partnerships",
            "moat": "Pre-built templates for trade-specific workflows",
            "ops_burden_estimate": "low",
            "compliance_risks": None
        }
    ]
    
    idea_ids = []
    for idea in ideas:
        response = requests.post(f"{API_BASE}/ideas", json=idea)
        if response.status_code == 200:
            idea_id = response.json()["id"]
            idea_ids.append(idea_id)
            print(f"  ✅ Idea: {idea['title'][:50]}...")
    
    # Step 5: Score and rank ideas
    print("\n📈 Step 5: Scoring and ranking ideas...")
    
    # Score individual ideas
    for idea_id in idea_ids:
        response = requests.post(f"{API_BASE}/ideas/{idea_id}/score")
        if response.status_code == 200:
            score = response.json()["total"]
            print(f"  ✅ Idea {idea_id}: Score {score:.1f}/100")
    
    # Rank all ideas
    for topic_id in topic_ids[:2]:
        response = requests.post(f"{API_BASE}/ideas/rank", json={"topic_id": topic_id})
        if response.status_code == 200:
            ranked = response.json()
            print(f"\n  📊 Topic {topic_id} Rankings:")
            for idea in ranked[:3]:
                print(f"     #{idea['rank']}: {idea['title'][:40]}... ({idea['total_score']:.1f})")
    
    # Step 6: Show evidence
    print("\n📋 Step 6: Evidence for top idea...")
    
    # Get top idea
    response = requests.get(f"{API_BASE}/ideas?min_score=0")
    if response.status_code == 200:
        ideas = response.json()
        if ideas:
            top_idea = ideas[0]
            print(f"\n  🏆 Top Idea: {top_idea['title']}")
            print(f"     Score: {top_idea['total_score']:.1f}/100")
            print(f"\n     Score Breakdown:")
            if top_idea.get('score_breakdown'):
                for key, val in top_idea['score_breakdown'].items():
                    if key != 'total':
                        print(f"       - {key}: {val}")
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open frontend/ideas.html to see ranked ideas")
    print("2. Add evidence links via API or UI")
    print("3. Adjust scoring weights in backend/scoring/weights.yaml")
    print("4. Run again with real API keys for live data")

if __name__ == "__main__":
    print("\n⚠️  Make sure the backend server is running:")
    print("   cd backend && python main.py\n")
    time.sleep(2)
    demo()
