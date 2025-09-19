# Sponsor Tools for Hackathon

This document outlines the sponsor tools available at our hackathon and provides concrete examples of how we're integrating them into PitchScoop, our pitch competition platform.

---

## 🧠 Context & Data Tools

### **Senso.ai** — Context OS
**What it does:** Ingests docs/emails/web content, normalizes to schema-safe JSON, builds agent-ready context.  
🌐 [https://docs.senso.ai](https://docs.senso.ai)

**How we use it in PitchScoop:**
```python
# Real example: Ingesting hackathon documentation and judge feedback
from senso import ContextOS

context_os = ContextOS(api_key=os.getenv('SENSO_API_KEY'))

# Ingest judge evaluation criteria and scoring rubrics
judge_context = await context_os.ingest_document(
    source="docs/judge_criteria.pdf",
    schema={
        "criteria": ["idea", "technical", "presentation", "market_potential"],
        "scoring_range": {"min": 1, "max": 10},
        "weight_factors": {"type": "object"}
    }
)

# Use normalized context for AI-powered pitch analysis
await analysis.score_pitch(session_id, context=judge_context)
```

### **Bright Data** — Real-time Web Scraping
**What it does:** Real-time web scraping & data pipelines for market/news/social feeds.  
🌐 [https://docs.brightdata.com](https://docs.brightdata.com)

**How we use it in PitchScoop:**
```python
# Real example: Scraping competitor analysis for pitch validation
from brightdata import WebScraperAPI

scraper = WebScraperAPI(token=os.getenv('BRIGHT_DATA_TOKEN'))

# Scrape market data for pitch idea validation
market_data = await scraper.collect(
    url="https://crunchbase.com/search/organizations",
    filters={
        "categories": pitch_idea.category,
        "founded_date": "2023-2024",
        "location": pitch_idea.target_market
    }
)

# Integrate into our scoring algorithm
competitor_score = await analysis.score_idea(
    pitch_content, 
    market_context=market_data
)
```

### **Apify** — Web Crawlers
**What it does:** Build and run web crawlers that return structured data.  
🌐 [https://apify.com](https://apify.com)

**How we use it in PitchScoop:**
```python
# Real example: Crawling startup databases for similar ideas
from apify_client import ApifyClient

client = ApifyClient(os.getenv('APIFY_TOKEN'))

# Run actor to crawl startup databases
run = client.actor("apify/website-content-crawler").call(
    run_input={
        "startUrls": ["https://angel.co/startups", "https://producthunt.com"],
        "globs": [{"glob": "**/*ai*"}, {"glob": "**/*pitch*"}],
        "maxCrawlDepth": 2
    }
)

# Use crawled data for uniqueness scoring
startup_landscape = client.dataset(run["defaultDatasetId"]).list_items()
uniqueness_score = await analysis.score_idea(pitch_transcript, 
                                           market_data=startup_landscape.items)
```

### **LlamaIndex** — LLM Data Framework
**What it does:** Framework to connect LLMs with external data (indexing + querying).  
🌐 [https://docs.llamaindex.ai](https://docs.llamaindex.ai)

**How we use it in PitchScoop:**
```python
# Real example: Building searchable knowledge base from pitch transcripts
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.storage.storage_context import StorageContext

# Index all pitch transcripts for similarity search
documents = []
for session in event_sessions:
    transcript = await pitches.get_session(session.id)
    documents.append(Document(text=transcript.content, metadata={
        "event_id": session.event_id,
        "team_name": session.team_name,
        "score": session.final_score
    }))

index = VectorStoreIndex.from_documents(documents)

# Query similar pitches for judges
similar_pitches = index.as_query_engine().query(
    "What are similar AI-powered solutions presented today?"
)
```

### **TigerData** — Time-Series Database
**What it does:** Time-series database for tracking metrics/events over time.  
🌐 [https://docs.tigerdata.com](https://docs.tigerdata.com)

**How we use it in PitchScoop:**
```python
# Real example: Tracking pitch performance metrics over time
import tigerdata

tiger = tigerdata.Client(api_key=os.getenv('TIGER_API_KEY'))

# Store real-time engagement metrics during pitch
await tiger.insert("pitch_engagement", {
    "timestamp": datetime.now(),
    "event_id": event_id,
    "session_id": session_id,
    "judge_attention_score": 8.5,
    "audience_reaction": 7.2,
    "technical_demo_success": True,
    "question_count": 3
})

# Query trends for leaderboard insights
engagement_trends = await tiger.query(
    "SELECT AVG(judge_attention_score) FROM pitch_engagement 
     WHERE event_id = ? GROUP BY session_id ORDER BY timestamp",
    [event_id]
)
```

### **Redis / RedisVL** — Vector Search
**What it does:** Fast in-memory DB with vector search for embeddings + semantic memory.  
🌐 [https://redis.io](https://redis.io) | [https://docs.redisvl.com](https://docs.redisvl.com)

**How we use it in PitchScoop:**
```python
# Real example: Already integrated! Semantic search for pitch analysis
from redisvl.api import SearchIndex
from redisvl.query import VectorQuery

# Create vector index for pitch embeddings (already in our codebase)
index = SearchIndex.from_yaml("pitch_schema.yaml")
index.connect(redis_url=os.getenv('REDIS_URL'))

# Store pitch embeddings
await index.load([{
    "session_id": session_id,
    "pitch_vector": pitch_embedding,
    "metadata": {"team": team_name, "category": category}
}])

# Semantic similarity search for judge recommendations
query = VectorQuery(
    vector=current_pitch_embedding,
    vector_field_name="pitch_vector",
    return_fields=["session_id", "team", "category"],
    num_results=5
)
similar_pitches = index.query(query)
```

---

## 🤖 AI & Agents

### **Gladia** — Multimodal Audio APIs
**What it does:** Speech-to-text, translation, transcription.  
🌐 [https://docs.gladia.io](https://docs.gladia.io)

**How we use it in PitchScoop:**
```python
# Real example: Already integrated! STT for pitch transcription
import httpx

async def transcribe_pitch(audio_file_path: str) -> str:
    """Already implemented in our codebase"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.gladia.io/v2/transcription/",
            headers={"X-Gladia-Key": os.getenv('GLADIA_API_KEY')},
            files={"audio": open(audio_file_path, "rb")},
            data={
                "language": "english",
                "output_format": "json",
                "enable_speaker_diarization": True
            }
        )
    return response.json()["prediction"]["text"]

# Used in our recording workflow
transcript = await transcribe_pitch(f"sessions/{session_id}/recording.wav")
await pitches.stop_recording(session_id, transcript=transcript)
```

### **MiniMax** — AI Agent Platform
**What it does:** Platform to build and orchestrate AI agents.  
🌐 [https://agent.minimax.io](https://agent.minimax.io)

**How we use it in PitchScoop:**
```python
# Real example: Creating specialized judge agents
from minimax import AgentOrchestrator

orchestrator = AgentOrchestrator(api_key=os.getenv('MINIMAX_KEY'))

# Create technical judge agent
tech_judge = await orchestrator.create_agent({
    "name": "TechnicalJudge",
    "personality": "Expert software architect focused on implementation feasibility",
    "criteria": ["code_quality", "architecture", "scalability", "tech_stack"],
    "scoring_range": [1, 10]
})

# Create business judge agent  
biz_judge = await orchestrator.create_agent({
    "name": "BusinessJudge", 
    "personality": "Seasoned VC partner evaluating market opportunity",
    "criteria": ["market_size", "revenue_model", "go_to_market", "competition"],
    "scoring_range": [1, 10]
})

# Orchestrate multi-agent pitch evaluation
evaluation = await orchestrator.evaluate_pitch(
    transcript=pitch_transcript,
    agents=[tech_judge, biz_judge],
    context={"event_type": "hackathon", "duration": "2_minutes"}
)
```

### **HoneyHive** — LLM Monitoring
**What it does:** Evaluate and monitor LLM agents (quality, reliability).  
🌐 [https://docs.honeyhive.ai](https://docs.honeyhive.ai)

**How we use it in PitchScoop:**
```python
# Real example: Monitoring our AI scoring system reliability
from honeyhive import HoneyHive

hh = HoneyHive(api_key=os.getenv('HONEYHIVE_KEY'))

# Wrap our existing scoring function with monitoring
@hh.monitor(project="pitchscoop-scoring")
async def score_pitch_monitored(session_id: str, transcript: str):
    """Enhanced version of our existing analysis.score_pitch"""
    result = await analysis.score_pitch(session_id, transcript)
    
    # Log metrics for quality assurance
    hh.log_feedback({
        "session_id": session_id,
        "scores": result.scores,
        "confidence": result.confidence,
        "processing_time": result.processing_time,
        "model_version": "azure-gpt-4"
    })
    
    return result

# Monitor bias in scoring across different team demographics
hh.create_evaluation_dataset("pitch_fairness", {
    "criteria": ["gender_bias", "accent_bias", "technical_domain_bias"],
    "sample_size": 100
})
```

### **Qodo** — AI Document Workflow
**What it does:** AI-driven document workflow automation.  
🌐 [https://docs.qodo.ai/qodo-documentation](https://docs.qodo.ai/qodo-documentation)

**How we use it in PitchScoop:**
```python
# Real example: Automated feedback report generation
from qodo import WorkflowEngine

workflow = WorkflowEngine(api_key=os.getenv('QODO_KEY'))

# Create automated feedback workflow
feedback_workflow = await workflow.create({
    "name": "PitchFeedbackGenerator",
    "inputs": ["pitch_transcript", "scores", "judge_notes"],
    "steps": [
        {
            "type": "analysis",
            "prompt": "Analyze pitch strengths and weaknesses"
        },
        {
            "type": "recommendations", 
            "prompt": "Generate 3 specific improvement recommendations"
        },
        {
            "type": "format",
            "template": "hackathon_feedback_template.md"
        }
    ],
    "output": "structured_feedback_report"
})

# Generate personalized feedback for each team
for session in completed_sessions:
    feedback = await workflow.execute("PitchFeedbackGenerator", {
        "pitch_transcript": session.transcript,
        "scores": session.ai_scores,
        "judge_notes": session.judge_feedback
    })
    await save_team_feedback(session.team_id, feedback)
```

### **Airia** — AI Knowledge Discovery
**What it does:** AI-powered knowledge discovery & enterprise search.  
🌐 [https://explore.airia.com/home](https://explore.airia.com/home)

**How we use it in PitchScoop:**
```python
# Real example: Intelligent search through hackathon resources
from airia import KnowledgeEngine

knowledge = KnowledgeEngine(api_key=os.getenv('AIRIA_KEY'))

# Index hackathon resources and previous pitch data
await knowledge.index_documents([
    "docs/hackathon_guidelines.pdf",
    "docs/sponsor_api_docs/",
    "historical_pitches/2023_winners.json",
    "judge_feedback_archive/"
])

# Smart Q&A for participants during development
async def hackathon_assistant(question: str) -> str:
    """AI assistant for hackathon participants"""
    answer = await knowledge.search(
        query=question,
        context="hackathon_resources",
        response_type="conversational"
    )
    return answer

# Examples of questions it can answer:
# "What APIs are available from sponsors?"
# "How did winning teams structure their pitches?"
# "What technical criteria do judges focus on?"
```

### **Horizon3.ai** — Security Testing
**What it does:** Automated security testing and vulnerability scanning.  
🌐 [https://docs.horizon3.ai](https://docs.horizon3.ai)

**How we use it in PitchScoop:**
```python
# Real example: Securing our platform and submitted projects
from horizon3 import SecurityScanner

scanner = SecurityScanner(api_key=os.getenv('HORIZON3_KEY'))

# Scan our PitchScoop platform
platform_scan = await scanner.scan_application({
    "target": "https://pitchscoop.hackathon.local:8000",
    "scan_type": "comprehensive",
    "include_api_endpoints": True,
    "check_authentication": True
})

# Optional: Scan team submissions (with permission)
async def scan_team_project(team_id: str, github_repo: str):
    """Scan team projects for security vulnerabilities"""
    if await get_team_consent(team_id, "security_scan"):
        results = await scanner.scan_repository({
            "repository": github_repo,
            "branch": "main",
            "scan_dependencies": True,
            "check_secrets": True
        })
        
        # Provide security feedback to teams
        await send_security_report(team_id, results)
        return results
    return None
```

---

## ⚙️ Dev & Auth

### **Stytch** — Authentication & Identity
**What it does:** Authentication & identity API (magic links, passkeys, OAuth, etc).  
🌐 [https://stytch.com/docs](https://stytch.com/docs)

**How we use it in PitchScoop:**
```python
# Real example: Hackathon participant authentication
import stytch

stytch_client = stytch.Client(
    project_id=os.getenv('STYTCH_PROJECT_ID'),
    secret=os.getenv('STYTCH_SECRET')
)

# Magic link authentication for hackathon registration
async def register_participant(email: str, team_name: str):
    """Register hackathon participant with magic link"""
    response = stytch_client.magic_links.email.login_or_create(
        email=email,
        login_magic_link_url="https://pitchscoop.hackathon.local/auth/magic",
        signup_magic_link_url="https://pitchscoop.hackathon.local/auth/magic",
        attributes={
            "team_name": team_name,
            "event_id": current_event_id,
            "role": "participant"
        }
    )
    return response

# OAuth for judges using GitHub/Google
async def authenticate_judge(oauth_token: str):
    """Authenticate judges via OAuth"""
    response = stytch_client.oauth.authenticate(
        token=oauth_token,
        session_duration_minutes=480  # 8 hours for hackathon duration
    )
    
    # Create judge session in our system
    judge_session = await create_judge_session(
        user_id=response.user_id,
        event_id=current_event_id,
        permissions=["score_pitches", "view_analytics"]
    )
    return judge_session
```

### **Speakeasy** (GetGram) — API Management
**What it does:** API management + SDK generation platform.  
🌐 [https://docs.getgram.ai](https://docs.getgram.ai)

**How we use it in PitchScoop:**
```yaml
# Real example: Generate SDKs for teams to integrate with our platform
# speakeasy-config.yaml
speakeasy_version: 1.0.0
management:
  docChecksum: "sha256:..."
  docVersion: "1.0.0"
  speakeasyVersion: "1.2.0"
generation:
  sdkClassName: "PitchScoop"
  maintainOpenAPIOrder: true
  usageSnippets:
    optionalPropertyRendering: withExample
targets:
  pitchscoop-python:
    target: python
    source: openapi.yaml
    output: ./sdks/python
  pitchscoop-typescript:
    target: typescript
    source: openapi.yaml  
    output: ./sdks/typescript
  pitchscoop-go:
    target: go
    source: openapi.yaml
    output: ./sdks/go
```

```python
# Generated SDK usage example for hackathon teams
from pitchscoop_sdk import PitchScoopClient

# Teams can easily integrate our scoring API
client = PitchScoopClient(api_key="team_api_key_123")

# Submit pitch for analysis
result = await client.pitches.submit_for_analysis(
    team_id="team_awesome",
    event_id="hackathon_2024",
    audio_file="./our_pitch.mp3",
    additional_info={
        "sponsor_tools_used": ["redis", "gladia", "stytch"],
        "github_repo": "https://github.com/team-awesome/hackathon-project"
    }
)

# Get real-time feedback
feedback = await client.feedback.get_analysis(result.submission_id)
print(f"Current score: {feedback.current_score}/10")
print(f"Suggestions: {feedback.improvements}")
```

---

## Integration Strategy

### How We're Combining These Tools

1. **Data Pipeline**: Bright Data → Senso.ai → RedisVL for market intelligence
2. **Audio Processing**: Gladia → Azure OpenAI → TigerData for pitch analysis  
3. **AI Orchestration**: MiniMax agents → HoneyHive monitoring → Qodo reports
4. **Security & Auth**: Stytch authentication → Horizon3 security scanning
5. **Developer Experience**: Speakeasy SDK generation for team integrations

### Real Implementation Timeline

- **Day 1**: Core platform with Gladia, Redis, Stytch integration
- **Day 2**: Add MiniMax judges, HoneyHive monitoring, TigerData metrics
- **Day 3**: Integrate market intelligence (Bright Data, Senso.ai, Airia)
- **Final Day**: Security scanning, SDK generation, automated reporting

### Sponsor Tool Integration Scoring

Teams using these sponsor tools get bonus points in our "Tools Integration" scoring criteria:

```python
def calculate_sponsor_tool_bonus(tools_used: List[str]) -> float:
    """Award bonus points for creative sponsor tool integration"""
    bonus_multipliers = {
        "senso_ai": 1.2,      # Context intelligence
        "bright_data": 1.15,   # Market research
        "gladia": 1.1,         # Audio processing
        "minimax": 1.3,        # AI agents
        "honeyhive": 1.1,      # AI monitoring
        "stytch": 1.1,         # Authentication
        "redis": 1.05,         # Performance
        # ... other tools
    }
    
    total_bonus = 1.0
    for tool in tools_used:
        total_bonus *= bonus_multipliers.get(tool, 1.0)
    
    return min(total_bonus, 1.5)  # Cap at 50% bonus
```

---

*This document will be updated as we integrate more sponsor tools throughout the hackathon.*