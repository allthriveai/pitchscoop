#!/usr/bin/env python3
"""
WHERE ARE THE SCORING RESULTS? 
This script shows you exactly where scoring results are stored and how to access them.
"""
import sys
import json
from datetime import datetime
sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')

def show_scoring_result_locations():
    print('🎯 SCORING RESULTS: Where They Live & How to Access Them')
    print('=' * 70)

    # 1. REDIS STORAGE LOCATIONS
    print('\n📦 REDIS STORAGE LOCATIONS')
    print('-' * 30)
    
    demo_event_id = "demo-event-123"
    demo_session_id = "session-456"
    demo_judge_id = "judge-789"
    
    storage_locations = {
        "Main Scoring Results": f"event:{demo_event_id}:scoring:{demo_session_id}",
        "Judge-Specific Results": f"event:{demo_event_id}:judge:{demo_judge_id}:scoring:{demo_session_id}",
        "Tool Analysis Results": f"event:{demo_event_id}:tool_analysis:{demo_session_id}",
        "Pitch Comparisons": f"event:{demo_event_id}:comparison:session1-session2-session3",
        "Enhanced Market Results": f"event:{demo_event_id}:enhanced_scoring:{demo_session_id}",
        "Presentation Analysis": f"event:{demo_event_id}:presentation_analysis:{demo_session_id}"
    }
    
    for name, key in storage_locations.items():
        print(f"   📍 {name}:")
        print(f"      Redis Key: {key}")
        print(f"      TTL: 24 hours (86400 seconds)")
        print()

    # 2. EXAMPLE SCORING RESULT STRUCTURE
    print('\n📊 EXAMPLE SCORING RESULT STRUCTURE')
    print('-' * 40)
    
    example_scoring_result = {
        "session_id": demo_session_id,
        "event_id": demo_event_id,
        "judge_id": demo_judge_id,
        "team_name": "Demo Team",
        "pitch_title": "AI Document Analysis Agent",
        "scoring_timestamp": datetime.now().isoformat(),
        "analysis": {
            "idea": {
                "score": 22.5,
                "max_score": 25,
                "unique_value_proposition": "Document quality analysis with AI reasoning",
                "vertical_focus": "Enterprise document management",
                "reasoning_capabilities": "Advanced NLP analysis of document structure",
                "action_capabilities": "Automated issue detection and report generation", 
                "tool_integration": "Seamless OpenAI, Qdrant, MinIO pipeline",
                "strengths": [
                    "Clear value proposition for enterprise market",
                    "Specific vertical focus on document quality"
                ],
                "areas_of_improvement": [
                    "More details on reasoning sophistication needed",
                    "Expand on competitive advantages"
                ]
            },
            "technical_implementation": {
                "score": 20.0,
                "max_score": 25,
                "novel_tool_use": "Multi-stage document processing pipeline",
                "technical_sophistication": "Good integration architecture",
                "surprise_factor": "Innovative document quality metrics",
                "implementation_quality": "Clean tool integration approach",
                "strengths": [
                    "Multi-tool integration shows technical depth",
                    "Clear architectural thinking"
                ],
                "areas_of_improvement": [
                    "More technical implementation details",
                    "Demonstrate more novel tool usage patterns"
                ]
            },
            "tool_use": {
                "score": 23.0,
                "max_score": 25,
                "sponsor_tools_used": ["OpenAI", "Qdrant", "MinIO"],
                "tool_count": 3,
                "integration_quality": "Well-integrated tool stack with clear purpose",
                "agentic_behavior": "Document analysis, quality assessment, report generation",
                "tool_synergy": "Tools complement each other for complete workflow",
                "strengths": [
                    "Meets 3+ sponsor tool requirement",
                    "Clear synergy between tool choices"
                ],
                "areas_of_improvement": [
                    "Could demonstrate more sophisticated agentic behaviors",
                    "Show more tool interaction complexity"
                ]
            },
            "presentation_delivery": {
                "score": 21.0,
                "max_score": 25,
                "demo_clarity": "Clear explanation of agent capabilities and workflow",
                "impact_demonstration": "Good explanation of business impact",
                "time_management": "Stayed within 3-minute limit effectively",
                "delivery_quality": "Professional presentation style",
                "agent_impact_shown": "Clear demonstration of value proposition",
                "strengths": [
                    "Clear and professional delivery",
                    "Good time management"
                ],
                "areas_of_improvement": [
                    "More interactive live demo elements",
                    "Show real-time agent actions"
                ]
            },
            "overall": {
                "total_score": 86.5,
                "max_total": 100,
                "percentage": 86.5,
                "ranking_tier": "very_good",
                "standout_features": [
                    "Strong tool integration strategy",
                    "Clear enterprise value proposition"
                ],
                "critical_improvements": [
                    "Enhanced technical depth demonstration",
                    "More sophisticated agentic behavior showcase"
                ],
                "judge_recommendation": "Excellent foundation with clear market focus. Strengthen technical demonstration and show more complex agent behaviors to reach top tier."
            }
        },
        "scoring_method": "azure_openai_langchain",
        "scoring_context": {
            "event_type": "hackathon",
            "sponsor_tools": ["OpenAI", "Qdrant", "MinIO", "Others"],
            "focus_areas": ["innovation", "technical_depth"]
        }
    }
    
    print("   🏆 TOTAL SCORE: 86.5/100 (86.5%)")
    print("   📊 Breakdown:")
    print(f"      • Idea: {example_scoring_result['analysis']['idea']['score']}/25")
    print(f"      • Technical: {example_scoring_result['analysis']['technical_implementation']['score']}/25")
    print(f"      • Tool Use: {example_scoring_result['analysis']['tool_use']['score']}/25")
    print(f"      • Presentation: {example_scoring_result['analysis']['presentation_delivery']['score']}/25")
    print(f"   🎖️  Ranking: {example_scoring_result['analysis']['overall']['ranking_tier'].replace('_', ' ').title()}")

    # 3. HOW TO ACCESS RESULTS - API ENDPOINTS
    print('\n🌐 HOW TO ACCESS RESULTS - API ENDPOINTS')
    print('-' * 42)
    
    api_endpoints = {
        "MCP Tool - Complete Scoring": {
            "method": "POST",
            "url": "http://localhost:8000/mcp/execute",
            "body": {
                "tool": "analysis.score_pitch",
                "arguments": {
                    "session_id": demo_session_id,
                    "event_id": demo_event_id,
                    "judge_id": demo_judge_id
                }
            },
            "returns": "Complete scoring analysis with all details"
        },
        
        "MCP Tool - Get Existing Scores": {
            "method": "POST", 
            "url": "http://localhost:8000/mcp/execute",
            "body": {
                "tool": "analysis.get_scores",
                "arguments": {
                    "session_id": demo_session_id,
                    "event_id": demo_event_id,
                    "include_details": True
                }
            },
            "returns": "Previously computed scoring results"
        },
        
        "REST API - Presentation Scoring": {
            "method": "GET",
            "url": f"http://localhost:8000/api/sessions/{demo_session_id}/scoring?event_id={demo_event_id}",
            "body": None,
            "returns": "Presentation delivery analysis with audio metrics"
        },
        
        "REST API - List All Sessions": {
            "method": "GET",
            "url": "http://localhost:8000/api/sessions",
            "body": None,
            "returns": "All recording sessions available for scoring"
        }
    }
    
    for endpoint_name, config in api_endpoints.items():
        print(f"   🔗 {endpoint_name}:")
        print(f"      Method: {config['method']}")
        print(f"      URL: {config['url']}")
        if config['body']:
            print(f"      Body: {json.dumps(config['body'], indent=8)}")
        print(f"      Returns: {config['returns']}")
        print()

    # 4. PROGRAMMATIC ACCESS EXAMPLE
    print('\n💻 PROGRAMMATIC ACCESS EXAMPLE')
    print('-' * 33)
    
    print("   Via MCP Tools (Python):")
    print(f"""
   from domains.scoring.mcp.scoring_mcp_tools import execute_scoring_mcp_tool
   
   # Score a pitch
   result = await execute_scoring_mcp_tool("analysis.score_pitch", {{
       "session_id": "{demo_session_id}",
       "event_id": "{demo_event_id}",
       "judge_id": "{demo_judge_id}"
   }})
   
   print(f"Total Score: {{result['scores']['overall']['total_score']}}/100")
   print(f"Ranking: {{result['scores']['overall']['ranking_tier']}}")
   """)

    print("   Via HTTP Requests (cURL):")
    print(f"""
   # Get complete scoring
   curl -X POST http://localhost:8000/mcp/execute \\
        -H "Content-Type: application/json" \\
        -d '{{"tool": "analysis.score_pitch", "arguments": {{"session_id": "{demo_session_id}", "event_id": "{demo_event_id}"}}}}'
   
   # Get existing scores
   curl -X POST http://localhost:8000/mcp/execute \\
        -H "Content-Type: application/json" \\
        -d '{{"tool": "analysis.get_scores", "arguments": {{"session_id": "{demo_session_id}", "event_id": "{demo_event_id}"}}}}'
   """)

    # 5. DATA PERSISTENCE & RETRIEVAL
    print('\n💾 DATA PERSISTENCE & RETRIEVAL')
    print('-' * 34)
    
    print("   ✅ Storage Duration: 24 hours (86400 seconds TTL)")
    print("   ✅ Storage Format: JSON in Redis")
    print("   ✅ Multi-tenant: Isolated by event_id")
    print("   ✅ Judge-specific: Optional judge_id namespace")
    print("   ✅ Backup-friendly: JSON format easily exportable")
    print("   ✅ Fast retrieval: Redis in-memory performance")

    # 6. EXAMPLE WORKFLOW FOR DEMO
    print('\n🎬 DEMO WORKFLOW - WHERE TO FIND YOUR SCORES')
    print('-' * 46)
    
    workflow_steps = [
        ("1. Record Pitch", "POST /mcp/execute → pitches.start_recording", "Creates session"),
        ("2. Stop Recording", "POST /mcp/execute → pitches.stop_recording", "Saves transcript"),
        ("3. Score Pitch", "POST /mcp/execute → analysis.score_pitch", "🎯 CREATES SCORES HERE"),
        ("4. View Results", "POST /mcp/execute → analysis.get_scores", "🎯 RETRIEVES SCORES HERE"),
        ("5. Get Details", f"GET /api/sessions/{demo_session_id}/scoring", "Additional analysis")
    ]
    
    for step, endpoint, result in workflow_steps:
        icon = "🎯" if "SCORES" in result else "📝"
        print(f"   {icon} {step}:")
        print(f"      API: {endpoint}")
        print(f"      Result: {result}")
        if "SCORES" in result:
            print(f"      📍 Redis Key: event:{{event_id}}:scoring:{{session_id}}")
        print()

    print('\n' + '=' * 70)
    print('🏆 FINAL ANSWER: Your scoring results will be at:')
    print()
    print(f'   📍 Redis Key: event:{{event_id}}:scoring:{{session_id}}')
    print(f'   🌐 API Endpoint: POST /mcp/execute → analysis.score_pitch')
    print(f'   📊 Format: Structured JSON with scores 0-100')
    print(f'   ⏰ Persistence: 24 hours in Redis')
    print(f'   🔍 Access: Via MCP tools or REST API')
    print()
    print('🚀 Your demo scoring pipeline is complete and accessible!')

if __name__ == "__main__":
    show_scoring_result_locations()