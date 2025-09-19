"""
LLM Request/Response Value Objects

Domain objects for handling LLM requests and responses in a structured way.
Provides type safety and validation for Azure OpenAI interactions.
"""
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LLMMessage:
    """A single message in an LLM conversation."""
    
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None  # Optional name for the message sender
    
    def __post_init__(self):
        """Validate message role."""
        valid_roles = {"system", "user", "assistant", "function"}
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role '{self.role}'. Must be one of: {valid_roles}")


@dataclass
class LLMRequest:
    """Request object for LLM API calls."""
    
    messages: List[LLMMessage]
    request_id: str = None
    temperature: float = 0.7
    max_tokens: int = 1500
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    user_id: Optional[str] = None  # For tracking
    
    def __post_init__(self):
        """Generate request ID if not provided and validate parameters."""
        if self.request_id is None:
            object.__setattr__(self, 'request_id', str(uuid.uuid4()))
        
        # Validate temperature
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        # Validate max_tokens
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        # Validate top_p
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
        
        # Validate penalties
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValueError("frequency_penalty must be between -2.0 and 2.0")
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValueError("presence_penalty must be between -2.0 and 2.0")
    
    @classmethod
    def create_simple(cls, prompt: str, **kwargs) -> "LLMRequest":
        """Create a simple request with a single user message."""
        return cls(
            messages=[LLMMessage(role="user", content=prompt)],
            **kwargs
        )
    
    @classmethod
    def create_chat(cls, system_prompt: str, user_message: str, **kwargs) -> "LLMRequest":
        """Create a request with system prompt and user message."""
        return cls(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_message)
            ],
            **kwargs
        )


@dataclass
class LLMResponse:
    """Response object from LLM API calls."""
    
    content: str
    finish_reason: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    model: str
    created_at: datetime
    metadata: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
    
    @property
    def is_success(self) -> bool:
        """Check if the response was successful."""
        return self.error is None and self.finish_reason != "error"


@dataclass
class PromptTemplate:
    """Template for generating structured prompts."""
    
    name: str
    template: str
    required_variables: List[str]
    description: str = ""
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        # Check required variables
        missing = [var for var in self.required_variables if var not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template variable not found: {e}")


# Prompt templates based on actual scoring criteria
PITCH_ANALYSIS_TEMPLATES = {
    "score_complete_pitch": PromptTemplate(
        name="score_complete_pitch",
        template="""
You are an expert judge for an AI agent pitch competition. Score this 3-minute pitch presentation based on the official criteria.

TRANSCRIPT:
{transcript}

SCORING CRITERIA (each worth 25% of total score):

1. **Idea (25%)** - Unique value proposition delivered by a vertical-specific agent using advanced reasoning, action, and tool use.
2. **Technical Implementation (25%)** - Surprise and inspire judges through novel use of tools in a unique way.
3. **Tool Use (25%)** - Integration of at least 3 sponsor tools to enable sophisticated agentic behavior.
4. **Presentation Delivery (25%)** - Present a live demo in 3-minutes that clearly demonstrates the agent's impact.

Provide scoring in JSON format:
{{
    "idea": {{
        "score": X.X,
        "max_score": 25,
        "unique_value_proposition": "what makes this agent unique",
        "vertical_focus": "what specific industry/domain",
        "reasoning_capabilities": "advanced reasoning demonstrated",
        "action_capabilities": "actions the agent can take",
        "tool_integration": "how tools enable the agent",
        "strengths": ["strength1", "strength2"],
        "areas_of_improvement": ["improvement1", "improvement2"]
    }},
    "technical_implementation": {{
        "score": X.X,
        "max_score": 25,
        "novel_tool_use": "innovative ways tools are used",
        "technical_sophistication": "complexity and elegance",
        "surprise_factor": "what surprised/inspired judges",
        "implementation_quality": "technical execution quality",
        "strengths": ["strength1", "strength2"],
        "areas_of_improvement": ["improvement1", "improvement2"]
    }},
    "tool_use": {{
        "score": X.X,
        "max_score": 25,
        "sponsor_tools_used": ["tool1", "tool2", "tool3+"],
        "tool_count": X,
        "integration_quality": "how well tools work together",
        "agentic_behavior": "sophisticated behaviors enabled",
        "tool_synergy": "how tools complement each other",
        "strengths": ["strength1", "strength2"],
        "areas_of_improvement": ["improvement1", "improvement2"]
    }},
    "presentation_delivery": {{
        "score": X.X,
        "max_score": 25,
        "demo_clarity": "how clear was the live demo",
        "impact_demonstration": "how well agent impact was demonstrated",
        "time_management": "stayed within 3 minutes",
        "delivery_quality": "presentation delivery effectiveness",
        "agent_impact_shown": "how clearly the agent's impact was demonstrated",
        "strengths": ["strength1", "strength2"],
        "areas_of_improvement": ["improvement1", "improvement2"]
    }},
    "overall": {{
        "total_score": X.X,
        "max_total": 100,
        "percentage": X.X,
        "ranking_tier": "excellent|very_good|good|needs_improvement",
        "standout_features": ["most impressive aspect 1", "most impressive aspect 2"],
        "critical_improvements": ["most important improvement 1", "most important improvement 2"],
        "judge_recommendation": "overall recommendation and rationale"
    }}
}}
        """.strip(),
        required_variables=["transcript"],
        description="Complete pitch scoring based on official competition criteria"
    ),
    
    "analyze_idea_uniqueness": PromptTemplate(
        name="analyze_idea_uniqueness",
        template="""
Analyze this AI agent pitch for idea uniqueness and value proposition strength.

TRANSCRIPT:
{transcript}

Focus on:
- Unique value proposition of the vertical-specific agent
- Advanced reasoning capabilities demonstrated
- Novel action capabilities
- Creative tool integration
- Market differentiation

Provide detailed analysis in JSON format:
{{
    "value_proposition": {{
        "clarity": "how clearly stated",
        "uniqueness": "what makes it unique",
        "vertical_specificity": "industry/domain focus",
        "competitive_advantage": "advantages over alternatives"
    }},
    "agent_capabilities": {{
        "reasoning": ["reasoning capability 1", "reasoning capability 2"],
        "actions": ["action capability 1", "action capability 2"],
        "tool_integration": "how tools enable agent behavior"
    }},
    "innovation_score": X.X,
    "recommendations": ["improvement 1", "improvement 2"]
}}
        """.strip(),
        required_variables=["transcript"],
        description="Deep analysis of idea uniqueness and value proposition"
    ),
    
    "analyze_tool_usage": PromptTemplate(
        name="analyze_tool_usage",
        template="""
Analyze the sponsor tool usage in this AI agent pitch presentation.

TRANSCRIPT:
{transcript}

REQUIREMENTS:
- Must integrate at least 3 sponsor tools
- Tools should enable sophisticated agentic behavior
- Integration should show synergy and innovation

Analyze in JSON format:
{{
    "tools_identified": [
        {{
            "tool_name": "name",
            "usage_description": "how it's used",
            "agentic_behavior_enabled": "what agent behaviors this enables",
            "innovation_level": "low|medium|high"
        }}
    ],
    "tool_count": X,
    "meets_minimum_requirement": true/false,
    "integration_quality": {{
        "synergy": "how well tools work together",
        "sophistication": "complexity of agentic behavior",
        "innovation": "novel usage patterns"
    }},
    "agentic_behaviors": ["behavior 1", "behavior 2", "behavior 3"],
    "tool_score": X.X,
    "improvement_suggestions": ["suggestion 1", "suggestion 2"]
}}
        """.strip(),
        required_variables=["transcript"],
        description="Analysis of sponsor tool integration and agentic behavior"
    ),
    
    "score_presentation_delivery_with_audio": PromptTemplate(
        name="score_presentation_delivery_with_audio",
        template="""
You are an expert judge analyzing presentation delivery for an AI agent pitch competition.
Score this presentation using BOTH transcript content AND audio delivery metrics from Gladia Audio Intelligence.

TRANSCRIPT:
{transcript}

AUDIO INTELLIGENCE METRICS:
- Speaking Rate: {words_per_minute} WPM (Assessment: {speaking_rate_assessment})
- Target WPM: {benchmark_wpm} (Difference: {pace_vs_target:+.0f} WPM)
- Filler Words: {filler_count} total ({filler_percentage:.1f}% of speech)
- Most Common Filler: "{most_common_filler}"
- Confidence Level: {confidence_score:.2f}/1.0 ({confidence_assessment})
- Energy Level: {energy_level}
- Delivery Grade: {professionalism_grade}

SCORING CRITERION:
**Presentation Delivery (25%)** - Present a live demo in 3-minutes that clearly demonstrates the agent's impact.

Analyze using BOTH content (from transcript) AND delivery (from audio metrics):

CONTENT ANALYSIS (40% weight):
- Demo clarity and explanation quality
- Agent impact demonstration effectiveness
- Technical depth and specificity
- Time management (3-minute constraint)

AUDIO DELIVERY ANALYSIS (60% weight):
- Speaking pace appropriateness ({speaking_rate_assessment} at {words_per_minute} WPM vs {benchmark_wpm} target)
- Professional delivery quality ({filler_percentage:.1f}% filler words - {professionalism_grade})
- Vocal confidence and energy ({confidence_assessment} confidence, {energy_level} energy)
- Overall presentation polish

Provide comprehensive analysis in JSON format:
{{
    "presentation_delivery": {{
        "score": X.X,
        "max_score": 25,
        "content_analysis": {{
            "demo_clarity": "assessment of demo explanation from transcript",
            "impact_demonstration": "how well agent impact was shown in content",
            "technical_depth": "technical detail level in explanation",
            "time_management": "adherence to 3-minute time limit",
            "content_score": X.X
        }},
        "audio_delivery_analysis": {{
            "speaking_pace": "{speaking_rate_assessment} at {words_per_minute} WPM (target: {benchmark_wpm})",
            "filler_control": "Professional delivery with {filler_percentage:.1f}% filler words ({professionalism_grade})",
            "vocal_confidence": "{confidence_assessment} confidence ({confidence_score:.2f}/1.0)",
            "energy_presence": "{energy_level} energy level",
            "delivery_polish": "Overall presentation delivery assessment",
            "audio_score": X.X
        }},
        "combined_analysis": {{
            "content_weight": "40%",
            "audio_weight": "60%",
            "final_score": X.X,
            "audio_enhanced_insights": "How audio metrics confirmed or enhanced content analysis"
        }},
        "strengths": ["strength1 with audio evidence", "strength2 from content analysis"],
        "areas_of_improvement": [
            "improvement1 with specific audio metrics (e.g., reduce {most_common_filler} usage)",
            "improvement2 from content analysis"
        ],
        "coaching_recommendations": [
            "Specific pace recommendation: {pace_recommendation}",
            "Filler word coaching: {filler_coaching}",
            "Content structure suggestion"
        ]
    }}
}}
        """.strip(),
        required_variables=[
            "transcript", "words_per_minute", "speaking_rate_assessment", 
            "benchmark_wpm", "pace_vs_target", "filler_count", "filler_percentage",
            "most_common_filler", "confidence_score", "confidence_assessment",
            "energy_level", "professionalism_grade", "pace_recommendation", "filler_coaching"
        ],
        description="Enhanced presentation delivery scoring with Audio Intelligence metrics"
    ),
    
    "generate_judge_feedback": PromptTemplate(
        name="generate_judge_feedback",
        template="""
You are a competition judge providing constructive feedback to this AI agent pitch team.

TRANSCRIPT:
{transcript}

PITCH SCORES:
{scores}

Provide encouraging but honest feedback in JSON format:
{{
    "overall_impression": "judge's overall impression and initial reaction",
    "strongest_aspects": [
        {{
            "category": "idea|technical|tools|presentation", 
            "achievement": "specific accomplishment",
            "impact": "why this impressed the judges"
        }}
    ],
    "improvement_opportunities": [
        {{
            "category": "idea|technical|tools|presentation",
            "issue": "specific area needing work",
            "suggestion": "concrete actionable advice",
            "priority": "high|medium|low"
        }}
    ],
    "technical_recommendations": [
        "specific technical suggestion 1",
        "specific technical suggestion 2"
    ],
    "presentation_recommendations": [
        "presentation improvement 1", 
        "presentation improvement 2"
    ],
    "next_steps": [
        "immediate next step 1",
        "immediate next step 2",
        "longer-term development goal"
    ],
    "encouragement": "motivational message recognizing their effort and potential",
    "competition_context": "how this pitch fits in the broader competition landscape"
}}
        """.strip(),
        required_variables=["transcript", "scores"],
        description="Judge feedback with constructive criticism and encouragement"
    )
}


def get_prompt_template(name: str) -> PromptTemplate:
    """Get a prompt template by name."""
    template = PITCH_ANALYSIS_TEMPLATES.get(name)
    if not template:
        available = list(PITCH_ANALYSIS_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{name}'. Available: {available}")
    return template