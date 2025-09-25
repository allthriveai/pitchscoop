#!/bin/bash
# PitchScoop Scoring API Test Script
# Run this to test the scoring endpoints with your frontend developer

BASE_URL="http://localhost:8000"

echo "🎯 PitchScoop Scoring API Test"
echo "=============================="

# Test 1: Health Check
echo ""
echo "1. Testing API Health..."
curl -s "$BASE_URL/mcp/health" | jq .

# Test 2: List Available MCP Tools
echo ""
echo "2. Available MCP Tools..."
curl -s "$BASE_URL/mcp/tools" | jq .

# Test 3: List Sessions
echo ""
echo "3. List Recording Sessions..."
curl -s "$BASE_URL/api/sessions" | jq .

# Test 4: Score a Pitch (Example)
echo ""
echo "4. Score a Pitch (Example Request)..."
echo "POST $BASE_URL/mcp/execute"
echo "Body:"
cat << 'EOF'
{
  "tool": "analysis.score_pitch",
  "arguments": {
    "session_id": "demo-session-123",
    "event_id": "demo-event-456",
    "judge_id": "judge-001"
  }
}
EOF

echo ""
echo "Expected Response Structure:"
cat << 'EOF'
{
  "session_id": "demo-session-123",
  "event_id": "demo-event-456", 
  "judge_id": "judge-001",
  "team_name": "Demo Team",
  "pitch_title": "AI Document Analysis Agent",
  "scores": {
    "idea": {
      "score": 22.5,
      "max_score": 25,
      "unique_value_proposition": "...",
      "strengths": ["..."],
      "areas_of_improvement": ["..."]
    },
    "technical_implementation": {
      "score": 20.0,
      "max_score": 25,
      "novel_tool_use": "...",
      "strengths": ["..."],
      "areas_of_improvement": ["..."]
    },
    "tool_use": {
      "score": 23.0,
      "max_score": 25,
      "sponsor_tools_used": ["OpenAI", "Qdrant", "MinIO"],
      "tool_count": 3,
      "strengths": ["..."],
      "areas_of_improvement": ["..."]
    },
    "presentation_delivery": {
      "score": 21.0,
      "max_score": 25,
      "demo_clarity": "...",
      "strengths": ["..."],
      "areas_of_improvement": ["..."]
    },
    "overall": {
      "total_score": 86.5,
      "max_total": 100,
      "percentage": 86.5,
      "ranking_tier": "very_good",
      "standout_features": ["..."],
      "critical_improvements": ["..."],
      "judge_recommendation": "..."
    }
  },
  "scoring_timestamp": "2024-01-15T10:05:00Z",
  "success": true
}
EOF

# Test 5: Get Existing Scores (Example)
echo ""
echo ""
echo "5. Get Existing Scores (Example Request)..."
echo "POST $BASE_URL/mcp/execute"
echo "Body:"
cat << 'EOF'
{
  "tool": "analysis.get_scores",
  "arguments": {
    "session_id": "demo-session-123",
    "event_id": "demo-event-456",
    "include_details": true
  }
}
EOF

# Test 6: Presentation Analysis (Example)
echo ""
echo ""
echo "6. Presentation Analysis with Audio Intelligence (Example)..."
echo "GET $BASE_URL/api/sessions/demo-session-123/scoring?event_id=demo-event-456"
echo ""
echo "Expected Response:"
cat << 'EOF'
{
  "session_id": "demo-session-123",
  "event_id": "demo-event-456",
  "team_name": "Demo Team", 
  "analysis_type": "presentation_delivery",
  "content_analysis": {
    "demo_clarity": "Clear demo explanation with 5 demo references",
    "estimated_wpm": 150.5,
    "content_score": 8.5
  },
  "audio_intelligence": {
    "available": true,
    "speech_pace": {
      "words_per_minute": 152,
      "speaking_rate_assessment": "optimal"
    },
    "delivery_quality": {
      "filler_percentage": 2.1,
      "professionalism_grade": "excellent"
    },
    "confidence_energy": {
      "confidence_score": 0.85,
      "confidence_assessment": "high"
    }
  },
  "presentation_delivery_score": {
    "final_score": 18.9,
    "max_score": 25.0
  },
  "insights": {
    "strengths": ["Clear delivery", "Optimal pace"],
    "areas_of_improvement": ["Reduce filler words"],
    "coaching_recommendations": ["Practice eliminating 'um'"]
  },
  "success": true
}
EOF

echo ""
echo ""
echo "🚀 FRONTEND INTEGRATION SUMMARY"
echo "==============================="
echo "✅ Base URL: $BASE_URL"
echo "✅ Main Endpoint: POST /mcp/execute"
echo "✅ Score Range: 0-100 (25 points per criterion)"
echo "✅ Ranking: excellent|very_good|good|needs_improvement"
echo "✅ Response Format: Always check 'success: true'"
echo "✅ Error Handling: 'error' field in responses"
echo ""
echo "📋 Required Parameters:"
echo "   • session_id (from recording)"
echo "   • event_id (for multi-tenancy)" 
echo "   • judge_id (optional)"
echo ""
echo "📊 Response Contains:"
echo "   • Individual criterion scores (/25 each)"
echo "   • Total score (/100)"
echo "   • Detailed feedback arrays"
echo "   • Professional recommendations"
echo "   • Audio intelligence metrics"
echo ""
echo "🔧 Frontend can display:"
echo "   • Score cards with progress bars"
echo "   • Ranking badges (very_good, excellent, etc)"
echo "   • Expandable feedback sections"
echo "   • Audio delivery insights"
echo ""
echo "📁 Full specification: FRONTEND_API_SPEC.md"