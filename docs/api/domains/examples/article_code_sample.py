# How Claude uses PitchScoop 🍦 via MCP

# Judge types:
"Score the Neural Ninjas pitch from today's hackathon"

# Claude calls via MCP:
result = mcp_client.call_tool(
    "analysis.score_pitch",
    {
        "session_id": "session_neural_ninjas_001",
        "event_id": "hackathon-2024"
    }
)

# Claude responds:
"""
**Neural Ninjas - Pitch Analysis**

📊 Overall Score: 87/100

• 💡 Idea: 22/25 - Strong AI agent concept
• 🔧 Technical: 21/25 - Solid RAG architecture
• 🛠️ Tools: 23/25 - Excellent sponsor integration
• 🎤 Presentation: 21/25 - Clear demo, timing issues

**Judge Recommendation:** Strong finalist candidate.
Recommend for next round.

Would you like me to compare with other teams?
"""

# Result: Claude becomes an AI judge assistant with professional scoring 🍒
