"""Message role inference with heuristics (FR-028)."""

import re
from typing import List, Optional

from blog_agent.storage.models import Message
from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


class RoleInference:
    """Heuristic-based role inference for messages."""

    # Question patterns (likely user)
    QUESTION_PATTERNS = [
        r"^[什麼如何為什麼怎麼].*[？?]",
        r"^[What How Why When Where].*[?]",
        r".*\?$",
        r"^請問",
        r"^我想",
        r"^我需要",
    ]

    # Answer patterns (likely assistant)
    ANSWER_PATTERNS = [
        r"^根據",
        r"^以下是",
        r"^我認為",
        r"^根據.*資料",
        r"^According to",
        r"^Based on",
    ]

    # Formatting cues (code blocks, lists suggest assistant)
    ASSISTANT_FORMATTING = [
        r"```",  # Code blocks
        r"^\d+\.",  # Numbered lists
        r"^[-*]",  # Bullet points
        r"^###",  # Markdown headers
    ]

    @classmethod
    def infer_role(
        cls,
        content: str,
        previous_role: Optional[str] = None,
        context: Optional[List[Message]] = None,
    ) -> str:
        """Infer message role using heuristics."""
        content_lower = content.lower().strip()

        # If previous role exists and content is very short, likely same role
        if previous_role and len(content) < 20:
            return previous_role

        # Check for question patterns
        for pattern in cls.QUESTION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return "user"

        # Check for answer patterns
        for pattern in cls.ANSWER_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return "assistant"

        # Check formatting (assistant tends to format better)
        formatting_score = sum(
            1 for pattern in cls.ASSISTANT_FORMATTING if re.search(pattern, content, re.MULTILINE)
        )
        if formatting_score >= 2:
            return "assistant"

        # Use context: alternate if previous role exists
        if previous_role:
            return "assistant" if previous_role == "user" else "user"

        # Default to user if unclear
        return "user"

    @classmethod
    def infer_roles_with_uncertainty(
        cls, messages: List[Message]
    ) -> tuple[List[Message], List[str]]:
        """Infer roles for all messages and return uncertainty markers."""
        inferred_messages = []
        uncertainties = []

        previous_role = None

        for msg in messages:
            # If role already set, use it
            if msg.role and msg.role in ["user", "assistant", "system"]:
                inferred_messages.append(msg)
                uncertainties.append("")
                previous_role = msg.role
                continue

            # Infer role
            inferred_role = cls.infer_role(msg.content, previous_role, inferred_messages)

            # Check uncertainty (simple heuristic: if very short or ambiguous)
            is_uncertain = len(msg.content) < 10 or (
                not any(
                    re.search(pattern, msg.content, re.IGNORECASE)
                    for pattern in cls.QUESTION_PATTERNS + cls.ANSWER_PATTERNS
                )
            )

            new_msg = Message(
                role=inferred_role,
                content=msg.content,
                timestamp=msg.timestamp,
            )

            inferred_messages.append(new_msg)
            uncertainties.append("uncertain" if is_uncertain else "")

            previous_role = inferred_role

        return inferred_messages, uncertainties

