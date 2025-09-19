"""
Document Processor - Convert application data to LlamaIndex documents

Handles conversion of various data types (rubrics, transcripts, team profiles)
into LlamaIndex Document objects for indexing and retrieval.
"""
import json
from typing import Dict, Any, List
from llama_index.core import Document
from datetime import datetime


class DocumentProcessor:
    """Service for processing and converting data to LlamaIndex documents."""
    
    @staticmethod
    def create_rubric_document(event_id: str, rubric_data: Dict[str, Any]) -> Document:
        """Convert event rubric to LlamaIndex document."""
        
        # Build comprehensive rubric content
        content_parts = [
            f"Event Scoring Rubric for Event ID: {event_id}",
            f"Event Name: {rubric_data.get('event_name', 'Unknown Event')}",
            "",
            "SCORING CRITERIA:"
        ]
        
        # Add criteria with descriptions and weights
        criteria = rubric_data.get('criteria', [])
        weights = rubric_data.get('weights', {})
        
        for i, criterion in enumerate(criteria, 1):
            weight = weights.get(criterion, 1.0)
            content_parts.extend([
                f"{i}. {criterion} (Weight: {weight})",
                f"   Description: {rubric_data.get('criteria_descriptions', {}).get(criterion, 'No description provided')}"
            ])
        
        # Add scoring guidelines
        if 'guidelines' in rubric_data:
            content_parts.extend([
                "",
                "SCORING GUIDELINES:",
                rubric_data['guidelines']
            ])
        
        # Add examples if available
        if 'examples' in rubric_data:
            content_parts.extend([
                "",
                "EXAMPLES:",
                json.dumps(rubric_data['examples'], indent=2)
            ])
        
        # Add scoring scale
        scale = rubric_data.get('scale', {'min': 1, 'max': 10})
        content_parts.extend([
            "",
            f"SCORING SCALE: {scale['min']} to {scale['max']}",
            f"Total Possible Score: {scale['max'] * len(criteria)}"
        ])
        
        content = "\n".join(content_parts)
        
        return Document(
            text=content,
            metadata={
                "document_type": "rubric",
                "event_id": event_id,
                "event_name": rubric_data.get('event_name', ''),
                "criteria_count": len(criteria),
                "total_weight": sum(weights.values()),
                "indexed_at": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def create_transcript_document(event_id: str, session_id: str, transcript_data: Dict[str, Any]) -> Document:
        """Convert pitch transcript to LlamaIndex document."""
        
        team_name = transcript_data.get('team_name', 'Unknown Team')
        pitch_title = transcript_data.get('pitch_title', 'Unknown Pitch')
        transcript_text = transcript_data.get('transcript_text', '')
        
        # Calculate basic metrics
        words = transcript_text.split() if transcript_text else []
        word_count = len(words)
        duration_seconds = transcript_data.get('duration_seconds', 0)
        words_per_minute = (word_count / duration_seconds * 60) if duration_seconds > 0 else 0
        
        content_parts = [
            f"PITCH TRANSCRIPT",
            f"Event ID: {event_id}",
            f"Session ID: {session_id}",
            f"Team: {team_name}",
            f"Pitch Title: {pitch_title}",
            "",
            "DELIVERY METRICS:",
            f"Duration: {duration_seconds} seconds ({duration_seconds/60:.1f} minutes)",
            f"Word Count: {word_count}",
            f"Speaking Rate: {words_per_minute:.1f} words per minute",
            "",
            "TRANSCRIPT:",
            transcript_text,
        ]
        
        # Add transcript segments if available
        if 'segments' in transcript_data:
            content_parts.extend([
                "",
                "DETAILED SEGMENTS:",
                json.dumps(transcript_data['segments'], indent=2)
            ])
        
        content = "\n".join(content_parts)
        
        return Document(
            text=content,
            metadata={
                "document_type": "transcript",
                "event_id": event_id,
                "session_id": session_id,
                "team_name": team_name,
                "pitch_title": pitch_title,
                "word_count": word_count,
                "duration_seconds": duration_seconds,
                "words_per_minute": words_per_minute,
                "indexed_at": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def create_team_document(event_id: str, team_data: Dict[str, Any]) -> Document:
        """Convert team profile to LlamaIndex document."""
        
        team_name = team_data.get('team_name', 'Unknown Team')
        
        content_parts = [
            f"TEAM PROFILE",
            f"Event ID: {event_id}",
            f"Team Name: {team_name}",
            ""
        ]
        
        # Add team members
        members = team_data.get('members', [])
        if members:
            content_parts.extend([
                "TEAM MEMBERS:",
                *[f"- {member}" for member in members]
            ])
        
        # Add team bio/description
        if 'bio' in team_data:
            content_parts.extend([
                "",
                "TEAM BIO:",
                team_data['bio']
            ])
        
        # Add focus areas
        if 'focus_areas' in team_data:
            content_parts.extend([
                "",
                "FOCUS AREAS:",
                *[f"- {area}" for area in team_data['focus_areas']]
            ])
        
        # Add previous experience
        if 'experience' in team_data:
            content_parts.extend([
                "",
                "EXPERIENCE:",
                team_data['experience']
            ])
        
        # Add skills
        if 'skills' in team_data:
            content_parts.extend([
                "",
                "SKILLS:",
                *[f"- {skill}" for skill in team_data['skills']]
            ])
        
        content = "\n".join(content_parts)
        
        return Document(
            text=content,
            metadata={
                "document_type": "team",
                "event_id": event_id,
                "team_name": team_name,
                "member_count": len(members),
                "has_bio": 'bio' in team_data,
                "focus_area_count": len(team_data.get('focus_areas', [])),
                "indexed_at": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def create_feedback_document(event_id: str, session_id: str, feedback_data: Dict[str, Any]) -> Document:
        """Convert generated feedback to LlamaIndex document."""
        
        team_name = feedback_data.get('team_name', 'Unknown Team')
        
        content_parts = [
            f"PITCH FEEDBACK REPORT",
            f"Event ID: {event_id}",
            f"Session ID: {session_id}",
            f"Team: {team_name}",
            ""
        ]
        
        # Add overall score
        if 'overall_score' in feedback_data:
            content_parts.extend([
                f"OVERALL SCORE: {feedback_data['overall_score']}",
                ""
            ])
        
        # Add criterion scores
        if 'scores' in feedback_data:
            content_parts.append("DETAILED SCORES:")
            for criterion, score_info in feedback_data['scores'].items():
                if isinstance(score_info, dict):
                    score = score_info.get('score', 0)
                    reasoning = score_info.get('reasoning', 'No reasoning provided')
                    content_parts.extend([
                        f"{criterion}: {score}",
                        f"  Reasoning: {reasoning}",
                        ""
                    ])
                else:
                    content_parts.append(f"{criterion}: {score_info}")
        
        # Add general feedback
        if 'feedback' in feedback_data:
            content_parts.extend([
                "",
                "GENERAL FEEDBACK:",
                feedback_data['feedback']
            ])
        
        # Add improvement suggestions
        if 'improvements' in feedback_data:
            content_parts.extend([
                "",
                "IMPROVEMENT SUGGESTIONS:",
                *[f"- {suggestion}" for suggestion in feedback_data['improvements']]
            ])
        
        content = "\n".join(content_parts)
        
        return Document(
            text=content,
            metadata={
                "document_type": "feedback",
                "event_id": event_id,
                "session_id": session_id,
                "team_name": team_name,
                "overall_score": feedback_data.get('overall_score'),
                "criterion_count": len(feedback_data.get('scores', {})),
                "has_improvements": 'improvements' in feedback_data,
                "indexed_at": datetime.utcnow().isoformat()
            }
        )
    
    @classmethod
    def create_multiple_documents(cls, document_configs: List[Dict[str, Any]]) -> List[Document]:
        """Create multiple documents from a list of configurations."""
        documents = []
        
        for config in document_configs:
            doc_type = config.get('type')
            
            if doc_type == 'rubric':
                doc = cls.create_rubric_document(
                    config['event_id'], 
                    config['data']
                )
            elif doc_type == 'transcript':
                doc = cls.create_transcript_document(
                    config['event_id'],
                    config['session_id'],
                    config['data']
                )
            elif doc_type == 'team':
                doc = cls.create_team_document(
                    config['event_id'],
                    config['data']
                )
            elif doc_type == 'feedback':
                doc = cls.create_feedback_document(
                    config['event_id'],
                    config['session_id'],
                    config['data']
                )
            else:
                continue  # Skip unknown document types
            
            documents.append(doc)
        
        return documents


# Global instance
document_processor = DocumentProcessor()