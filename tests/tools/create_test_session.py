#!/usr/bin/env python3
"""Create test session with transcript for scoring."""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root and api directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

import redis.asyncio as redis

async def create_test_session():
    """Create a test session with transcript for scoring tests."""
    
    client = redis.from_url('redis://redis:6379/0', decode_responses=True)
    
    transcript_text = ("Hello judges, we're CryptoFlow, an automated cryptocurrency trading agent. "
                      "Our AI agent uses advanced machine learning algorithms to analyze market patterns "
                      "and execute trades automatically. We integrate three key sponsor tools: OpenAI for "
                      "market sentiment analysis from news and social media, Qdrant for historical trading "
                      "pattern recognition, and MinIO for secure storage of trading data and strategies. "
                      "Our agent processes real-time market data, news sentiment, and technical indicators "
                      "to make split-second trading decisions. We've implemented sophisticated risk management "
                      "using LangChain to create decision trees that consider multiple market factors. "
                      "In backtesting, our agent achieved 34% returns over the past 6 months while traditional "
                      "strategies averaged 8%. Our agent trades 24/7 and has processed over 10,000 trades "
                      "with a 67% success rate. Thank you.")
    
    test_session = {
        'session_id': 'test-scoring-session-001',
        'event_id': 'test-hackathon-2024',
        'team_name': 'CryptoFlow AI',
        'pitch_title': 'Automated Cryptocurrency Trading Agent',
        'status': 'completed',
        'created_at': '2024-01-15T10:00:00Z',
        'completed_at': '2024-01-15T10:03:00Z',
        'final_transcript': {
            'total_text': transcript_text,
            'segments_count': 5,
            'segments': []
        }
    }
    
    key = 'event:test-hackathon-2024:session:test-scoring-session-001'
    await client.setex(key, 3600, json.dumps(test_session))
    
    print("✅ Created test session with transcript")
    print(f"   Session ID: test-scoring-session-001")
    print(f"   Event ID: test-hackathon-2024")
    print(f"   Team: CryptoFlow AI")
    print(f"   Transcript length: {len(transcript_text)} chars")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(create_test_session())