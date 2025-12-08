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

    type: Literal["structured", "role-play", "chain-of-thought"]
    prompt: str = Field(..., description="The improved prompt text")
    reasoning: str = Field(..., description="Reasoning for why this version is better")


class PromptCandidatesResponse(BaseModel):
    """Response containing alternative prompt candidates."""

    candidates: List[PromptCandidateItem] = Field(
        default_factory=list, description="List of alternative prompt candidates"
    )

