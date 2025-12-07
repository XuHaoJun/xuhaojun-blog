"""Conversation log parsers."""

from blog_agent.parsers.csv_parser import CSVParser
from blog_agent.parsers.json_parser import JSONParser
from blog_agent.parsers.markdown_parser import MarkdownParser

__all__ = ["MarkdownParser", "JSONParser", "CSVParser", "ParserFactory"]


class ParserFactory:
    """Factory for creating appropriate parser based on file format."""

    PARSERS = {
        "markdown": MarkdownParser,
        "json": JSONParser,
        "csv": CSVParser,
        "text": MarkdownParser,  # Treat plain text as Markdown
    }

    @classmethod
    def create_parser(cls, file_format: str):
        """Create parser for given format."""
        parser_class = cls.PARSERS.get(file_format.lower())
        if not parser_class:
            raise ValueError(f"Unsupported file format: {file_format}")

        return parser_class()

    @classmethod
    def detect_format(cls, file_path: str, content: Optional[str] = None) -> str:
        """Auto-detect file format from path and/or content."""
        import os

        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        ext_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".json": "json",
            ".csv": "csv",
            ".txt": "text",
        }

        if ext in ext_map:
            return ext_map[ext]

        # Check content if provided
        if content:
            # Check for JSON
            if content.strip().startswith("{") or content.strip().startswith("["):
                try:
                    import json

                    json.loads(content)
                    return "json"
                except Exception:
                    pass

            # Check for Markdown (has ## headers)
            if "##" in content[:500]:
                return "markdown"

            # Check for CSV (has commas and newlines)
            if "," in content and "\n" in content:
                return "csv"

        # Default to text/markdown
        return "text"


# Import Optional
from typing import Optional

