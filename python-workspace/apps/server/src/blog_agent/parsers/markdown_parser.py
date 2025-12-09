"""Markdown conversation log parser."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from blog_agent.storage.models import ConversationLog, Message
from blog_agent.utils.errors import ValidationError
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class MarkdownParser:
    """Parser for Markdown format conversation logs."""

    # Common role markers in Chinese/English
    # Note: Patterns match role names without ## prefix since we split by ^##\s+
    ROLE_PATTERNS = {
        "user": [
            r"^使用者\s*$",
            r"^User\s*$",
            r"^用戶\s*$",
            r"^提问\s*$",
            r"^提问者\s*$",
        ],
        "assistant": [
            r"^Gemini\s*$",
            r"^Assistant\s*$",
            r"^AI\s*$",
            r"^回答\s*$",
            r"^回答者\s*$",
            r"^ChatGPT\s*$",
            r"^Claude\s*$",
        ],
        "system": [
            r"^System\s*$",
            r"^系統\s*$",
        ],
    }

    def parse(self, content: str, file_path: str) -> ConversationLog:
        """Parse Markdown conversation log."""
        try:
            # Extract frontmatter if present
            frontmatter, body = self._extract_frontmatter(content)

            # Parse messages
            messages = self._parse_messages(body)

            # Extract metadata
            metadata = self._extract_metadata(frontmatter, content)

            # Detect language
            language = self._detect_language(messages)

            parsed_content = {
                "messages": [msg.model_dump(mode='json') for msg in messages],
                "frontmatter": frontmatter,
            }

            return ConversationLog(
                file_path=file_path,
                file_format="markdown",
                raw_content=content,
                parsed_content=parsed_content,
                metadata=metadata,
                language=language,
                message_count=len(messages),
            )

        except Exception as e:
            logger.error("Failed to parse Markdown", error=str(e), exc_info=True)
            raise ValidationError(
                field="content",
                message=f"Failed to parse Markdown format: {str(e)}",
            ) from e

    def _extract_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter if present."""
        frontmatter = {}
        body = content

        # Check for frontmatter (--- at start)
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml

                    frontmatter = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                except Exception as e:
                    logger.warning("Failed to parse frontmatter", error=str(e))
                    # Continue without frontmatter

        return frontmatter, body

    def _parse_messages(self, body: str) -> List[Message]:
        """Parse messages from Markdown body."""
        messages = []

        # Split by role markers
        sections = re.split(r"^##\s+", body, flags=re.MULTILINE)

        for section in sections:
            if not section.strip():
                continue

            # Try to identify role from first line
            lines = section.split("\n", 1)
            if len(lines) < 2:
                continue

            role_line = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""

            if not content:
                continue

            # Determine role
            role = self._infer_role(role_line, content)

            # Extract timestamp if present (from frontmatter or content)
            timestamp = None

            messages.append(
                Message(
                    role=role,
                    content=content,
                    timestamp=timestamp,
                )
            )

        return messages

    def _infer_role(self, role_line: str, content: str) -> str:
        """Infer message role from role line and content."""
        role_line_lower = role_line.lower()

        # Check against known patterns
        for role, patterns in self.ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, role_line, re.IGNORECASE):
                    return role

        # Heuristic: if starts with question words, likely user
        question_words = ["什麼", "如何", "為什麼", "怎麼", "what", "how", "why", "when", "where"]
        content_lower = content.lower()
        if any(content_lower.startswith(word.lower()) for word in question_words):
            return "user"

        # Default to assistant if unclear
        return "assistant"

    def _extract_metadata(self, frontmatter: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Extract metadata from frontmatter and content."""
        metadata = {}

        # Copy frontmatter fields
        if frontmatter:
            metadata.update(frontmatter)
            # Serialize datetime objects to ISO strings for consistency
            for key, value in metadata.items():
                if isinstance(value, datetime):
                    # Format as ISO 8601 with Z suffix if UTC, matching YAML export format
                    if value.tzinfo is not None:
                        offset = value.utcoffset()
                        if offset is not None and offset.total_seconds() == 0:
                            # UTC timezone - use Z suffix, format milliseconds (3 digits)
                            metadata[key] = value.strftime("%Y-%m-%dT%H:%M:%S") + f".{value.microsecond // 1000:03d}Z"
                        else:
                            metadata[key] = value.isoformat()
                    else:
                        metadata[key] = value.isoformat()

        # Extract title from markdown only if not already in frontmatter
        if "title" not in metadata:
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()

        return metadata

    def _detect_language(self, messages: List[Message]) -> Optional[str]:
        """Detect language from messages."""
        if not messages:
            return None

        # Simple heuristic: check for Chinese characters
        chinese_chars = 0
        total_chars = 0

        for msg in messages[:5]:  # Check first 5 messages
            for char in msg.content:
                total_chars += 1
                if "\u4e00" <= char <= "\u9fff":
                    chinese_chars += 1

        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            return "zh-TW"

        return "en"

