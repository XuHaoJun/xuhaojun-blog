"""Markdown formatter with frontmatter support for blog posts."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from blog_agent.storage.models import BlogPost, PromptSuggestion
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class MarkdownFormatter:
    """Formatter for generating Markdown with frontmatter from blog posts."""

    def format(self, blog_post: BlogPost, prompt_suggestion: Optional[PromptSuggestion] = None) -> str:
        """
        Format blog post as Markdown with YAML frontmatter.
        
        Args:
            blog_post: The blog post to format
            prompt_suggestion: Optional prompt suggestion to include (T081)
            
        Returns:
            Markdown string with frontmatter
        """
        frontmatter = self._generate_frontmatter(blog_post, prompt_suggestion)
        content = blog_post.content
        
        # T081: Format prompt suggestions as side-by-side comparison if present
        if prompt_suggestion and prompt_suggestion.original_prompt:
            prompt_section = self._format_prompt_suggestions(prompt_suggestion)
            content = f"{content}\n\n{prompt_section}"
        
        # Combine frontmatter and content
        markdown = f"---\n{frontmatter}---\n\n{content}\n"
        
        return markdown

    def _format_prompt_suggestions(self, prompt_suggestion: PromptSuggestion) -> str:
        """
        T081: Format prompt suggestions as side-by-side comparison.
        
        Creates a formatted section showing original prompt vs improved versions.
        """
        section = "## 提示詞優化建議\n\n"
        
        # Original prompt
        section += f"### 原始提示詞\n\n```\n{prompt_suggestion.original_prompt}\n```\n\n"
        
        # Analysis
        if prompt_suggestion.analysis:
            section += f"### 分析\n\n{prompt_suggestion.analysis}\n\n"
        
        # Improved versions (side-by-side comparison)
        if prompt_suggestion.better_candidates:
            section += "### 改進版本\n\n"
            for i, candidate in enumerate(prompt_suggestion.better_candidates[:5], 1):
                section += f"#### 版本 {i}\n\n```\n{candidate}\n```\n\n"
        
        # Reasoning
        if prompt_suggestion.reasoning:
            section += f"### 改進理由\n\n{prompt_suggestion.reasoning}\n\n"
        
        return section

    def _generate_frontmatter(self, blog_post: BlogPost, prompt_suggestion: Optional[PromptSuggestion] = None) -> str:
        """
        Generate YAML frontmatter from blog post metadata.
        
        Args:
            blog_post: The blog post to generate frontmatter for
            
        Returns:
            YAML frontmatter string
        """
        frontmatter_data: Dict[str, Any] = {}
        
        # Required fields (FR-005)
        frontmatter_data["title"] = blog_post.title
        frontmatter_data["summary"] = blog_post.summary
        if blog_post.tags:
            frontmatter_data["tags"] = blog_post.tags
        
        # Status
        frontmatter_data["status"] = blog_post.status
        
        # Dates
        if blog_post.created_at:
            frontmatter_data["created_at"] = blog_post.created_at.isoformat()
        if blog_post.updated_at:
            frontmatter_data["updated_at"] = blog_post.updated_at.isoformat()
        
        # Additional metadata from blog_post.metadata
        if blog_post.metadata:
            # Preserve conversation timestamps (FR-015)
            if "conversation_timestamps" in blog_post.metadata:
                frontmatter_data["conversation_timestamps"] = blog_post.metadata["conversation_timestamps"]
            
            # Preserve participants (FR-015)
            if "conversation_participants" in blog_post.metadata:
                frontmatter_data["conversation_participants"] = blog_post.metadata["conversation_participants"]
            
            # Language
            if "language" in blog_post.metadata:
                frontmatter_data["language"] = blog_post.metadata["language"]
            
            # Message count
            if "message_count" in blog_post.metadata:
                frontmatter_data["message_count"] = blog_post.metadata["message_count"]
            
            # Key insights and core concepts (for reference)
            if "key_insights" in blog_post.metadata:
                frontmatter_data["key_insights"] = blog_post.metadata["key_insights"]
            if "core_concepts" in blog_post.metadata:
                frontmatter_data["core_concepts"] = blog_post.metadata["core_concepts"]
            
            # Prompt suggestion metadata (T081)
            if prompt_suggestion:
                frontmatter_data["has_prompt_suggestions"] = bool(prompt_suggestion.better_candidates)
                frontmatter_data["prompt_candidates_count"] = len(prompt_suggestion.better_candidates)
        
        # Convert to YAML format (simple implementation)
        yaml_lines = []
        for key, value in frontmatter_data.items():
            if isinstance(value, str):
                # Escape special characters in strings
                escaped_value = value.replace('"', '\\"').replace('\n', '\\n')
                yaml_lines.append(f'{key}: "{escaped_value}"')
            elif isinstance(value, list):
                # Format list
                if value:
                    yaml_lines.append(f"{key}:")
                    for item in value:
                        escaped_item = str(item).replace('"', '\\"').replace('\n', '\\n')
                        yaml_lines.append(f'  - "{escaped_item}"')
                else:
                    yaml_lines.append(f"{key}: []")
            elif isinstance(value, dict):
                # Format nested dict
                yaml_lines.append(f"{key}:")
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, str):
                        escaped_nested = nested_value.replace('"', '\\"').replace('\n', '\\n')
                        yaml_lines.append(f'  {nested_key}: "{escaped_nested}"')
                    else:
                        yaml_lines.append(f"  {nested_key}: {nested_value}")
            elif value is None:
                yaml_lines.append(f"{key}: null")
            else:
                yaml_lines.append(f"{key}: {value}")
        
        return "\n".join(yaml_lines) + "\n"

