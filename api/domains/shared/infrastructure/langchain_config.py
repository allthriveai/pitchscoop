"""
LangChain Configuration and Integration

Provides LangChain integration with Azure OpenAI for advanced prompting,
chains, and structured outputs. Supports multi-tenant isolation.
"""
import os
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema.output_parser import StrOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ...shared.value_objects.llm_request import LLMMessage, get_prompt_template
from .logging import get_logger, log_with_context


class PitchScoreOutput(BaseModel):
    """Structured output for pitch scoring - matches LLM nested output format."""
    
    idea: Dict[str, Any] = Field(description="Idea scoring details")
    technical_implementation: Dict[str, Any] = Field(description="Technical scoring details")
    tool_use: Dict[str, Any] = Field(description="Tool usage scoring details")
    presentation_delivery: Dict[str, Any] = Field(description="Presentation delivery scoring with optional audio intelligence")
    overall: Dict[str, Any] = Field(description="Overall scoring summary")


class EnhancedPresentationDeliveryOutput(BaseModel):
    """Structured output for presentation delivery analysis with Audio Intelligence."""
    
    score: float = Field(description="Presentation delivery score (0-25)")
    max_score: float = Field(description="Maximum possible score (25)")
    
    content_analysis: Dict[str, Any] = Field(description="Content analysis from transcript")
    audio_delivery_analysis: Optional[Dict[str, Any]] = Field(description="Audio delivery analysis from Gladia AI")
    combined_analysis: Optional[Dict[str, Any]] = Field(description="Combined scoring methodology")
    
    strengths: List[str] = Field(description="Identified presentation strengths")
    areas_of_improvement: List[str] = Field(description="Areas for improvement")
    coaching_recommendations: List[str] = Field(description="Actionable coaching suggestions")
    
    audio_intelligence_available: bool = Field(description="Whether Audio Intelligence data was used")
    audio_intelligence_metrics: Optional[Dict[str, Any]] = Field(description="Raw audio intelligence metrics")


class ToolAnalysisOutput(BaseModel):
    """Structured output for tool usage analysis."""
    
    tools_identified: List[str] = Field(description="List of sponsor tools identified")
    tool_count: int = Field(description="Number of tools used")
    meets_requirement: bool = Field(description="Whether it meets 3+ tool requirement")
    agentic_behaviors: List[str] = Field(description="Sophisticated agentic behaviors enabled")
    innovation_level: str = Field(description="Overall innovation level: low, medium, high")
    recommendations: List[str] = Field(description="Improvement recommendations")


class FeedbackOutput(BaseModel):
    """Structured output for judge feedback."""
    
    overall_impression: str = Field(description="Judge's overall impression")
    strongest_aspects: List[str] = Field(description="The pitch's strongest aspects")
    improvement_opportunities: List[str] = Field(description="Key areas for improvement")
    next_steps: List[str] = Field(description="Actionable next steps")
    encouragement: str = Field(description="Motivational message for the team")


@dataclass
class LangChainConfig:
    """Configuration for LangChain with Azure OpenAI."""
    
    azure_endpoint: str
    api_key: str
    deployment_name: str
    api_version: str
    temperature: float = 0.3  # Lower temperature for more consistent scoring
    max_tokens: int = 2000
    
    @classmethod
    def from_environment(cls) -> "LangChainConfig":
        """Create configuration from environment variables."""
        endpoint = os.getenv("SYSTEM_LLM_AZURE_ENDPOINT")
        api_key = os.getenv("SYSTEM_LLM_AZURE_API_KEY")
        deployment = os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT")
        api_version = os.getenv("SYSTEM_LLM_AZURE_API_VERSION")
        
        if not all([endpoint, api_key, deployment, api_version]):
            missing = []
            if not endpoint: missing.append("SYSTEM_LLM_AZURE_ENDPOINT")
            if not api_key: missing.append("SYSTEM_LLM_AZURE_API_KEY") 
            if not deployment: missing.append("SYSTEM_LLM_AZURE_DEPLOYMENT")
            if not api_version: missing.append("SYSTEM_LLM_AZURE_API_VERSION")
            
            raise ValueError(f"Missing required Azure OpenAI environment variables: {missing}")
        
        return cls(
            azure_endpoint=endpoint,
            api_key=api_key,
            deployment_name=deployment,
            api_version=api_version
        )


class PitchAnalysisChains:
    """LangChain chains for pitch analysis."""
    
    def __init__(self, config: Optional[LangChainConfig] = None):
        """Initialize pitch analysis chains."""
        self.config = config or LangChainConfig.from_environment()
        self._llm = None
        self._chains = {}
    
    def get_llm(self) -> AzureChatOpenAI:
        """Get or create Azure OpenAI LLM instance."""
        if self._llm is None:
            self._llm = AzureChatOpenAI(
                azure_endpoint=self.config.azure_endpoint,
                api_key=self.config.api_key,
                azure_deployment=self.config.deployment_name,
                api_version=self.config.api_version,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
        return self._llm
    
    def create_scoring_chain(self) -> LLMChain:
        """Create chain for complete pitch scoring with structured output."""
        if "scoring" not in self._chains:
            # Get prompt template
            template = get_prompt_template("score_complete_pitch")
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    "You are an expert judge for AI agent pitch competitions. "
                    "Provide accurate, fair scoring based on the official criteria. "
                    "Be thorough but constructive in your evaluation."
                ),
                HumanMessagePromptTemplate.from_template(template.template)
            ])
            
            # Create parser for structured output
            parser = PydanticOutputParser(pydantic_object=PitchScoreOutput)
            
            # Create chain
            self._chains["scoring"] = LLMChain(
                llm=self.get_llm(),
                prompt=prompt,
                output_parser=parser,
                verbose=False
            )
        
        return self._chains["scoring"]
    
    def create_tool_analysis_chain(self) -> LLMChain:
        """Create chain for analyzing sponsor tool usage."""
        if "tool_analysis" not in self._chains:
            template = get_prompt_template("analyze_tool_usage")
            
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    "You are an expert at analyzing AI agent tool integration. "
                    "Focus on identifying sponsor tools and how they enable agentic behavior. "
                    "Be specific about tool names and usage patterns."
                ),
                HumanMessagePromptTemplate.from_template(template.template)
            ])
            
            parser = PydanticOutputParser(pydantic_object=ToolAnalysisOutput)
            
            self._chains["tool_analysis"] = LLMChain(
                llm=self.get_llm(),
                prompt=prompt,
                output_parser=parser,
                verbose=False
            )
        
        return self._chains["tool_analysis"]
    
    def create_feedback_chain(self) -> LLMChain:
        """Create chain for generating judge feedback."""
        if "feedback" not in self._chains:
            template = get_prompt_template("generate_judge_feedback")
            
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(
                    "You are a supportive but honest competition judge. "
                    "Provide constructive feedback that helps teams improve while "
                    "recognizing their efforts and achievements. Be encouraging but specific."
                ),
                HumanMessagePromptTemplate.from_template(template.template)
            ])
            
            parser = PydanticOutputParser(pydantic_object=FeedbackOutput)
            
            self._chains["feedback"] = LLMChain(
                llm=self.get_llm(),
                prompt=prompt,
                output_parser=parser,
                verbose=False
            )
        
        return self._chains["feedback"]
    
    async def score_pitch(self, transcript: str, event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Score a complete pitch using structured analysis.
        
        Args:
            transcript: The pitch transcript to analyze
            event_id: Organization ID for multi-tenant isolation
            
        Returns:
            Structured pitch scores and analysis
        """
        logger = get_logger("langchain")
        start_time = time.time()
        
        log_with_context(
            logger, "INFO", "Starting LangChain pitch scoring",
            event_id=event_id,
            operation="score_pitch",
            transcript_length=len(transcript),
            transcript_word_count=len(transcript.split())
        )
        
        try:
            # Create scoring chain with error handling
            try:
                chain = self.create_scoring_chain()
                log_with_context(
                    logger, "DEBUG", "Scoring chain created successfully",
                    event_id=event_id,
                    operation="create_scoring_chain"
                )
            except Exception as chain_error:
                log_with_context(
                    logger, "ERROR", f"Failed to create scoring chain: {str(chain_error)}",
                    event_id=event_id,
                    operation="create_scoring_chain"
                )
                return {
                    "success": False,
                    "error": f"Chain creation failed: {str(chain_error)}",
                    "event_id": event_id,
                    "analysis_type": "complete_scoring",
                    "error_type": "chain_creation_error"
                }
            
            # Execute chain with detailed logging
            log_with_context(
                logger, "DEBUG", "Invoking LangChain scoring analysis",
                event_id=event_id,
                operation="chain_invoke"
            )
            
            try:
                result = await chain.ainvoke({"transcript": transcript})
                
                log_with_context(
                    logger, "DEBUG", "LangChain scoring completed successfully",
                    event_id=event_id,
                    operation="chain_invoke",
                    result_type=type(result).__name__,
                    has_dict_method=hasattr(result, 'dict')
                )
                
            except Exception as invoke_error:
                duration_ms = (time.time() - start_time) * 1000
                log_with_context(
                    logger, "ERROR", f"LangChain chain invocation failed: {str(invoke_error)}",
                    event_id=event_id,
                    operation="chain_invoke",
                    duration_ms=duration_ms,
                    transcript_length=len(transcript),
                    error_type=type(invoke_error).__name__
                )
                return {
                    "success": False,
                    "error": f"Chain invocation failed: {str(invoke_error)}",
                    "event_id": event_id,
                    "analysis_type": "complete_scoring",
                    "error_type": "chain_invocation_error"
                }
            
            # Process result
            try:
                analysis_data = result.dict() if hasattr(result, 'dict') else result
                duration_ms = (time.time() - start_time) * 1000
                
                log_with_context(
                    logger, "INFO", "Pitch scoring completed successfully",
                    event_id=event_id,
                    operation="score_pitch",
                    duration_ms=duration_ms,
                    analysis_keys=list(analysis_data.keys()) if isinstance(analysis_data, dict) else None
                )
                
                return {
                    "success": True,
                    "analysis": analysis_data,
                    "event_id": event_id,
                    "analysis_type": "complete_scoring",
                    "duration_ms": duration_ms
                }
                
            except Exception as result_error:
                duration_ms = (time.time() - start_time) * 1000
                log_with_context(
                    logger, "ERROR", f"Failed to process scoring result: {str(result_error)}",
                    event_id=event_id,
                    operation="result_processing",
                    duration_ms=duration_ms
                )
                return {
                    "success": False,
                    "error": f"Result processing failed: {str(result_error)}",
                    "event_id": event_id,
                    "analysis_type": "complete_scoring",
                    "error_type": "result_processing_error"
                }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_with_context(
                logger, "ERROR", f"Unexpected error in pitch scoring: {str(e)}",
                event_id=event_id,
                operation="score_pitch",
                duration_ms=duration_ms,
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": f"Pitch scoring failed: {str(e)}",
                "event_id": event_id,
                "analysis_type": "complete_scoring",
                "error_type": "unexpected_error"
            }
    
    async def analyze_tool_usage(self, transcript: str, event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze sponsor tool usage in the pitch.
        
        Args:
            transcript: The pitch transcript to analyze
            event_id: Organization ID for multi-tenant isolation
            
        Returns:
            Tool usage analysis results
        """
        try:
            chain = self.create_tool_analysis_chain()
            
            # Skip metadata for Azure OpenAI compatibility
            # llm = self.get_llm()
            # if event_id:
            #     llm.model_kwargs = llm.model_kwargs or {}
            #     llm.model_kwargs["metadata"] = {"event_id": event_id}
            
            result = await chain.ainvoke({"transcript": transcript})
            
            return {
                "success": True,
                "analysis": result.dict() if hasattr(result, 'dict') else result,
                "event_id": event_id,
                "analysis_type": "tool_usage"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool usage analysis failed: {str(e)}",
                "event_id": event_id,
                "analysis_type": "tool_usage"
            }
    
    async def generate_feedback(self, transcript: str, scores: Dict[str, Any], event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate judge feedback for the pitch.
        
        Args:
            transcript: The pitch transcript
            scores: Previous scoring results
            event_id: Organization ID for multi-tenant isolation
            
        Returns:
            Structured feedback from judges
        """
        try:
            chain = self.create_feedback_chain()
            
            
            import json
            scores_json = json.dumps(scores, indent=2)
            
            result = await chain.ainvoke({"transcript": transcript, "scores": scores_json})
            
            return {
                "success": True,
                "feedback": result.dict() if hasattr(result, 'dict') else result,
                "event_id": event_id,
                "analysis_type": "judge_feedback"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Feedback generation failed: {str(e)}",
                "event_id": event_id,
                "analysis_type": "judge_feedback"
            }


# Global chains instance
_pitch_analysis_chains: Optional[PitchAnalysisChains] = None


def get_pitch_analysis_chains() -> PitchAnalysisChains:
    """Get global pitch analysis chains instance."""
    global _pitch_analysis_chains
    if _pitch_analysis_chains is None:
        _pitch_analysis_chains = PitchAnalysisChains()
    return _pitch_analysis_chains


# For testing
async def test_langchain_integration():
    """Test LangChain integration with sample data."""
    print("Testing LangChain integration...")
    
    try:
        chains = get_pitch_analysis_chains()
        
        # Sample transcript for testing
        sample_transcript = """
        Hi, I'm presenting CanaryQA, our AI agent for document quality assurance.
        We've built a vertical-specific agent that uses advanced reasoning to analyze 
        technical documentation. Our agent integrates three sponsor tools: OpenAI for 
        language processing, Qdrant for vector search, and MinIO for document storage.
        The agent can automatically detect quality issues, suggest improvements, and 
        generate reports. Thank you.
        """
        
        # Test scoring
        print("Testing pitch scoring...")
        score_result = await chains.score_pitch(sample_transcript, event_id="test-org")
        print(f"Scoring result: {score_result}")
        
        # Test tool analysis
        print("\\nTesting tool analysis...")
        tool_result = await chains.analyze_tool_usage(sample_transcript, event_id="test-org")
        print(f"Tool analysis result: {tool_result}")
        
        print("✅ LangChain integration test completed!")
        
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_langchain_integration())