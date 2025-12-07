"""CSV conversation log parser."""

import csv
import io
from typing import Any, Dict, List

from blog_agent.storage.models import ConversationLog, Message
from blog_agent.utils.errors import ValidationError
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class CSVParser:
    """Parser for CSV format conversation logs."""

    def parse(self, content: str, file_path: str) -> ConversationLog:
        """Parse CSV conversation log."""
        try:
            # Try to detect delimiter
            delimiter = self._detect_delimiter(content)

            # Parse CSV
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            rows = list(reader)

            if not rows:
                raise ValidationError(
                    field="content",
                    message="CSV file is empty or has no data rows",
                )

            # Extract messages
            messages = self._parse_rows(rows)

            parsed_content = {
                "messages": [msg.model_dump() for msg in messages],
                "rows": rows,
            }

            return ConversationLog(
                file_path=file_path,
                file_format="csv",
                raw_content=content,
                parsed_content=parsed_content,
                message_count=len(messages),
            )

        except Exception as e:
            logger.error("Failed to parse CSV", error=str(e), exc_info=True)
            raise ValidationError(
                field="content",
                message=f"Failed to parse CSV format: {str(e)}",
            ) from e

    def _detect_delimiter(self, content: str) -> str:
        """Detect CSV delimiter."""
        # Check first line
        first_line = content.split("\n")[0] if "\n" in content else content

        # Common delimiters
        delimiters = [",", ";", "\t", "|"]

        for delim in delimiters:
            if delim in first_line:
                return delim

        return ","  # Default

    def _parse_rows(self, rows: List[Dict[str, Any]]) -> List[Message]:
        """Parse CSV rows into messages."""
        messages = []

        # Common column name variations
        role_columns = ["role", "type", "speaker", "sender", "from"]
        content_columns = ["content", "text", "message", "body", "value"]

        for row in rows:
            # Find role column
            role = None
            for col in role_columns:
                if col in row and row[col]:
                    role = str(row[col]).lower()
                    break

            if not role:
                role = "user"  # Default

            # Find content column
            content = None
            for col in content_columns:
                if col in row and row[col]:
                    content = str(row[col])
                    break

            if not content:
                continue  # Skip empty rows

            # Normalize role
            if role in ["user", "使用者", "用戶", "提问", "提问者"]:
                role = "user"
            elif role in ["assistant", "ai", "gemini", "chatgpt", "claude", "回答", "回答者"]:
                role = "assistant"
            elif role in ["system", "系統"]:
                role = "system"
            else:
                role = "user"  # Default

            messages.append(
                Message(
                    role=role,
                    content=content,
                )
            )

        return messages

