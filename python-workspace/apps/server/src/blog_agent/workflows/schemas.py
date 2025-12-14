"""Pydantic schemas for structured LLM outputs in workflows."""

from typing import List, Literal

from pydantic import BaseModel, Field


# Extender schemas
class KnowledgeGap(BaseModel):
    """Represents a knowledge gap identified in content."""

    type: str = Field(..., description="Type of gap (e.g., missing_context, unclear_concept)")
    description: str = Field(..., description="Description of the gap")
    location: str = Field(..., description="Where in the content the gap appears")
    query: str = Field(..., description="Search query to find information about this gap")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority level")


class KnowledgeGapResponse(BaseModel):
    """Response containing identified knowledge gaps."""

    gaps: List[KnowledgeGap] = Field(default_factory=list, description="List of identified knowledge gaps")


# Reviewer schemas
class LogicalGap(BaseModel):
    """Represents a logical gap in content."""

    type: str = Field(..., description="Type of logical gap (e.g., concept_jump, argument_gap)")
    description: str = Field(..., description="Description of the logical gap")
    location: str = Field(..., description="Where in the content the gap appears")
    severity: Literal["high", "medium", "low"] = Field(..., description="Severity level")


class LogicalGapsResponse(BaseModel):
    """Response containing detected logical gaps."""

    gaps: List[LogicalGap] = Field(default_factory=list, description="List of detected logical gaps")


class FactualInconsistency(BaseModel):
    """Represents a factual inconsistency in content."""

    type: str = Field(..., description="Type of inconsistency (e.g., contradiction, fact_mismatch)")
    description: str = Field(..., description="Description of the inconsistency")
    claim1: str = Field(..., description="First contradictory claim")
    claim2: str = Field(..., description="Second contradictory claim")
    severity: Literal["high", "medium", "low"] = Field(..., description="Severity level")


class FactualInconsistenciesResponse(BaseModel):
    """Response containing detected factual inconsistencies."""

    inconsistencies: List[FactualInconsistency] = Field(
        default_factory=list, description="List of detected factual inconsistencies"
    )


class UnclearExplanation(BaseModel):
    """Represents an unclear explanation in content."""

    type: str = Field(..., description="Type of unclear point (e.g., undefined_term, unclear_step)")
    description: str = Field(..., description="Description of the unclear point")
    location: str = Field(..., description="Where in the content the unclear point appears")
    suggestion: str = Field(..., description="Suggestion for improvement")
    severity: Literal["high", "medium", "low"] = Field(..., description="Severity level")


class UnclearExplanationsResponse(BaseModel):
    """Response containing detected unclear explanations."""

    unclear_points: List[UnclearExplanation] = Field(
        default_factory=list, description="List of detected unclear explanations"
    )


# Prompt analyzer schemas (for structured JSON parsing)
class PromptCandidateItem(BaseModel):
    """Represents a prompt candidate item in structured output."""

    type: str = Field(..., description="Strategy type (e.g., 'few-shot', 'chain-of-thought', 'expert-persona', 'minimalist', etc.)")
    prompt: str = Field(..., description="The improved prompt text")
    reasoning: str = Field(..., description="Reasoning for why this version is better")


class PromptCandidatesResponse(BaseModel):
    """Response containing alternative prompt candidates."""

    candidates: List[PromptCandidateItem] = Field(
        default_factory=list, description="List of alternative prompt candidates"
    )


# Fact-checking schemas
class FactCheckAnalysis(BaseModel):
    """Represents fact-check analysis result for a claim."""

    verification_status: Literal["verified", "contradicted", "unclear", "unverifiable"] = Field(
        ..., description="Whether the claim is verified, contradicted, unclear, or unverifiable"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Confidence level in the verification"
    )
    evidence: str = Field(
        ..., description="Key evidence from sources that supports or contradicts the claim"
    )
    contradictions: List[str] = Field(
        default_factory=list, description="List of contradictions found in sources"
    )
    reasoning: str = Field(
        ..., description="Reasoning for the verification status"
    )


class FactCheckAnalysisResponse(BaseModel):
    """Response containing fact-check analysis."""

    analysis: FactCheckAnalysis = Field(..., description="Fact-check analysis result")


# Extractor schemas (Soul Overview aligned)
class ConversationAnalysis(BaseModel):
    """Represents structured analysis of conversation content.
    
    Aligned with Anthropic's Soul Overview principles:
    - Focuses on underlying goals, not just surface content
    - Provides contextual value assessment
    - Ensures structured, precise output
    """

    key_insights: List[str] = Field(
        default_factory=list,
        description="3-5 個對話中的核心洞察，專注於解決問題的本質和使用者的潛在目標 (Underlying Goals)"
    )
    core_concepts: List[str] = Field(
        default_factory=list,
        description="對話中涉及的技術術語或關鍵主題，不超過 10 個"
    )
    user_intent: str = Field(
        default="",
        description="使用者的潛在目標 (Underlying Goal) - 使用者表面問了什麼，但他真正想解決的深層問題是什麼？"
    )
    substantive_score: int = Field(
        default=5,
        description="對話的實質價值評分 (1-10)，基於是否包含具體的問題解決、知識交換或創意發想",
        ge=1,
        le=10
    )

