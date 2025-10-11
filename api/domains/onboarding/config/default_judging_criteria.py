"""
Default Judging Criteria Configuration

Defines the standard judging categories that all events start with.
Event organizers can adjust weights and add custom categories.
"""

from typing import List, Dict, Any


DEFAULT_JUDGING_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "idea",
        "name": "Idea Category",
        "weight": 0.25,
        "adjustable": True,
        "criteria": [
            {
                "id": "wow_factor",
                "text": "Wow Factor: Innovative, Unique",
                "description": "Is the idea creative and stands out from typical solutions?"
            },
            {
                "id": "feasible",
                "text": "Feasible: Can be built and marketed",
                "description": "Is the solution realistic and achievable within constraints?"
            },
            {
                "id": "competitive",
                "text": "Competitive: Doesn't have a lot of competition",
                "description": "Does the solution address an underserved market or unique angle?"
            }
        ]
    },
    {
        "id": "technical",
        "name": "Technical Implementation",
        "weight": 0.25,
        "adjustable": True,
        "criteria": [
            {
                "id": "built_today",
                "text": "Did you build the code today?",
                "description": "Was actual development work completed during the event?"
            },
            {
                "id": "code_works",
                "text": "Does the code work?",
                "description": "Is the implementation functional and demonstrable?"
            },
            {
                "id": "code_quality",
                "text": "Does the code make sense?",
                "description": "Is the code well-structured and maintainable?"
            },
            {
                "id": "innovative_code",
                "text": "Is the code innovative and inspiring?",
                "description": "Does the technical approach show creativity or novel solutions?"
            }
        ]
    },
    {
        "id": "tools",
        "name": "Tool Use",
        "weight": 0.20,
        "adjustable": True,
        "criteria": [
            {
                "id": "used_tools",
                "text": "Did you use the hackathon sponsor tools?",
                "description": "Were the designated sponsor technologies incorporated?"
            },
            {
                "id": "innovative_tools",
                "text": "Did you use the hackathon sponsor tools in an innovative and comprehensive manner?",
                "description": "Was the tool integration creative and thorough?"
            }
        ]
    },
    {
        "id": "presentation",
        "name": "Presentation",
        "weight": 0.30,
        "adjustable": True,
        "criteria": [
            {
                "id": "engaging",
                "text": "Dynamic and passionate: Engaged the audience",
                "description": "Did the presenter show enthusiasm and capture attention?"
            },
            {
                "id": "clear",
                "text": "Clear and comprehensible: Didn't speak too fast or too slow",
                "description": "Was the delivery easy to follow and well-paced?"
            },
            {
                "id": "structured",
                "text": "Flow has beginning, middle and end, highlighting problem solved in a clear manner and explaining how solution works clearly",
                "description": "Was there a logical narrative structure that effectively communicated the value?"
            }
        ]
    }
]


def get_default_judging_categories() -> List[Dict[str, Any]]:
    """Get a copy of default judging categories"""
    import copy
    return copy.deepcopy(DEFAULT_JUDGING_CATEGORIES)


def validate_judging_weights(categories: List[Dict[str, Any]]) -> bool:
    """
    Validate that judging category weights sum to 1.0 (or close to it).
    
    Returns:
        bool: True if weights are valid
    """
    total_weight = sum(cat.get("weight", 0) for cat in categories)
    # Allow small floating point errors
    return abs(total_weight - 1.0) < 0.01


def normalize_judging_weights(categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize judging category weights to sum to 1.0.
    Useful when organizer adds custom categories.
    
    Returns:
        List of categories with normalized weights
    """
    total_weight = sum(cat.get("weight", 0) for cat in categories)
    
    if total_weight == 0:
        # Equal weights if all are 0
        equal_weight = 1.0 / len(categories)
        for cat in categories:
            cat["weight"] = equal_weight
    else:
        # Normalize to sum to 1.0
        for cat in categories:
            cat["weight"] = cat.get("weight", 0) / total_weight
    
    return categories


DEFAULT_REQUIRED_FIELDS = [
    "user_name",
    "team_name", 
    "project_name",
    "project_description"
]


DEFAULT_HELP_TEXT = {
    "event_types": {
        "practice": "Informal practice session - Perfect for trying out ideas",
        "hackathon": "Single day coding competition - Build and compete with teams",
        "investor_pitch": "Pitch to potential investors- Present your startup",
        "job_interview": "Practice for job interviews - Prepare for technical interviews"
    },
    "judging_weights": "Adjust the importance of each category. Higher weights have more impact on final scores.",
    "custom_categories": "Add your own judging criteria specific to your event type or focus area (e.g., Sustainability, User Experience, Business Viability).",
    "project_description": "Briefly describe what your project does and what problem it solves. This helps judges understand your pitch context."
}
