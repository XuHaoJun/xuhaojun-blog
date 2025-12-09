"""Pydantic models for blog agent system."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in a conversation."""

    role: str  # "user", "system", or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ConversationLog(BaseModel):
    """Represents an input conversation log."""

    id: Optional[UUID] = None
    file_path: str
    file_format: str = Field(..., pattern="^(markdown|json|csv|text)$")
    raw_content: str
    parsed_content: Dict[str, Any]
    content_hash: Optional[str] = None  # SHA-256 hash of file content for change detection (FR-031)
    metadata: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    message_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BlogPost(BaseModel):
    """Represents a generated blog post."""

    id: Optional[UUID] = None
    conversation_log_id: UUID
    title: str = Field(..., min_length=1)  # Required, non-empty (FR-005)
    summary: str = Field(..., min_length=1)  # Required, non-empty (FR-005)
    tags: List[str] = Field(default_factory=list)  # Required but can be empty (FR-005)
    content: str  # Markdown format
    metadata: Optional[Dict[str, Any]] = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProcessingHistory(BaseModel):
    """Represents processing history record."""

    id: Optional[UUID] = None
    conversation_log_id: UUID
    blog_post_id: Optional[UUID] = None
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    error_message: Optional[str] = None
    processing_steps: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ContentExtract(BaseModel):
    """Represents intermediate content extraction result."""

    id: Optional[UUID] = None
    conversation_log_id: UUID
    key_insights: List[str] = Field(default_factory=list)
    core_concepts: List[str] = Field(default_factory=list)
    filtered_content: str
    created_at: Optional[datetime] = None


class ReviewFindings(BaseModel):
    """Represents review/critique findings."""

    id: Optional[UUID] = None
    content_extract_id: UUID
    issues: Dict[str, Any]  # Structured issues
    improvement_suggestions: List[str] = Field(default_factory=list)
    fact_checking_needs: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class PromptCandidate(BaseModel):
    """Represents a structured prompt candidate with type and reasoning."""

    type: Literal["structured", "role-play", "chain-of-thought"]
    prompt: str
    reasoning: str


class PromptSuggestion(BaseModel):
    """Represents prompt analysis and optimization result."""

    id: Optional[UUID] = None
    conversation_log_id: UUID
    original_prompt: str
    analysis: str
    better_candidates: List[PromptCandidate] = Field(..., min_length=3)  # At least 3 structured candidates (FR-012)
    reasoning: str  # Overall reasoning (kept for backward compatibility)
    expected_effect: Optional[str] = None  # Expected effect description (UI/UX support)
    created_at: Optional[datetime] = None


class ContentBlock(BaseModel):
    """Represents a structured content block for blog posts (UI/UX support)."""

    id: Optional[UUID] = None
    blog_post_id: UUID
    block_order: int  # Order in the article (starting from 0)
    text: str  # Article content in Markdown format
    prompt_suggestion_id: Optional[UUID] = None  # Optional: associated prompt suggestion
    created_at: Optional[datetime] = None

