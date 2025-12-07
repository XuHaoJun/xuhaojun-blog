"""JSON conversation log parser."""

import json
from typing import Any, Dict, List

from blog_agent.storage.models import ConversationLog, Message
from blog_agent.utils.errors import ValidationError
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class JSONParser:
    """Parser for JSON format conversation logs."""

    def parse(self, content: str, file_path: str) -> ConversationLog:
        """Parse JSON conversation log."""
        try:
            # Try to parse JSON
            data = json.loads(content)

            # Handle different JSON structures
            if isinstance(data, list):
                messages = self._parse_list_format(data)
            elif isinstance(data, dict):
                messages = self._parse_dict_format(data)
            else:
                raise ValidationError(
                    field="content",
                    message="JSON format not recognized",
                )

            parsed_content = {
                "messages": [msg.model_dump() for msg in messages],
                "raw_data": data,
            }

            return ConversationLog(
                file_path=file_path,
                file_format="json",
                raw_content=content,
                parsed_content=parsed_content,
                metadata=data.get("metadata", {}) if isinstance(data, dict) else {},
                message_count=len(messages),
            )

        except json.JSONDecodeError as e:
            # Try to auto-fix common JSON issues (FR-026)
            try:
                fixed_content = self._auto_fix_json(content)
                return self.parse(fixed_content, file_path)
            except Exception:
                logger.error("Failed to parse JSON", error=str(e), exc_info=True)
                raise ValidationError(
                    field="content",
                    message=f"Invalid JSON format: {str(e)}",
                ) from e
        except Exception as e:
            logger.error("Failed to parse JSON", error=str(e), exc_info=True)
            raise ValidationError(
                field="content",
                message=f"Failed to parse JSON format: {str(e)}",
            ) from e

    def _parse_list_format(self, data: List[Dict[str, Any]]) -> List[Message]:
        """Parse list of message objects."""
        messages = []
        for item in data:
            role = item.get("role", "user")
            content = item.get("content", item.get("text", ""))
            timestamp = item.get("timestamp")

            if content:
                messages.append(
                    Message(
                        role=role,
                        content=str(content),
                        timestamp=timestamp,
                    )
                )

        return messages

    def _parse_dict_format(self, data: Dict[str, Any]) -> List[Message]:
        """Parse dict with messages array."""
        messages = []

        # Try common keys
        messages_data = data.get("messages", data.get("conversation", data.get("chat", [])))

        if isinstance(messages_data, list):
            return self._parse_list_format(messages_data)

        # If no messages array, try to extract from other fields
        if "user" in data and "assistant" in data:
            messages.append(
                Message(
                    role="user",
                    content=str(data["user"]),
                )
            )
            messages.append(
                Message(
                    role="assistant",
                    content=str(data["assistant"]),
                )
            )

        return messages

    def _auto_fix_json(self, content: str) -> str:
        """Auto-fix common JSON format issues (FR-026)."""
        fixed = content

        # Fix trailing commas
        fixed = re.sub(r",\s*}", "}", fixed)
        fixed = re.sub(r",\s*]", "]", fixed)

        # Fix single quotes to double quotes
        fixed = re.sub(r"'([^']*)':", r'"\1":', fixed)
        fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)

        # Fix unquoted keys
        fixed = re.sub(r"(\w+):", r'"\1":', fixed)

        return fixed


# Import regex at module level
import re

