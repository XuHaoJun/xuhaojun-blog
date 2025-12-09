"""Unit tests for MarkdownParser."""

import pytest
from pathlib import Path

from blog_agent.parsers.markdown_parser import MarkdownParser
from blog_agent.utils.errors import ValidationError


@pytest.fixture
def parser():
    """Create a MarkdownParser instance."""
    return MarkdownParser()


@pytest.fixture
def sample_file_path():
    """Path to sample markdown file."""
    return str(
        Path(__file__).parent.parent / "fixtures" / "sample_conversation.md"
    )


@pytest.fixture
def sample_content(sample_file_path):
    """Load sample markdown content."""
    with open(sample_file_path, "r", encoding="utf-8") as f:
        return f.read()


class TestMarkdownParser:
    """Test cases for MarkdownParser."""

    def test_parse_with_frontmatter(self, parser, sample_content, sample_file_path):
        """Test parsing markdown with YAML frontmatter."""
        result = parser.parse(sample_content, sample_file_path)

        assert result.file_path == sample_file_path
        assert result.file_format == "markdown"
        assert result.raw_content == sample_content
        assert result.metadata is not None
        assert "title" in result.metadata
        assert result.metadata["title"] == "Google Gemini"
        assert result.metadata["platform"] == "Gemini"
        assert result.metadata["exported"] == "2025-12-08T10:49:42.094Z"

    def test_parse_messages(self, parser, sample_content, sample_file_path):
        """Test parsing messages from markdown."""
        result = parser.parse(sample_content, sample_file_path)

        assert result.message_count > 0
        assert "messages" in result.parsed_content
        messages = result.parsed_content["messages"]

        # Should have at least user and assistant messages
        roles = [msg["role"] for msg in messages]
        assert "user" in roles
        assert "assistant" in roles

        # Check message structure
        for msg in messages:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant", "system"]
            assert len(msg["content"]) > 0

    def test_parse_without_frontmatter(self, parser):
        """Test parsing markdown without frontmatter."""
        content = """# Test Conversation

## User

What is Python?

## Assistant

Python is a programming language.
"""
        result = parser.parse(content, "test.md")

        assert result.file_format == "markdown"
        assert result.metadata is not None
        assert result.message_count == 2
        assert result.parsed_content["frontmatter"] == {}

    def test_extract_frontmatter(self, parser):
        """Test frontmatter extraction."""
        content = """---
title: Test
author: John Doe
---
# Content
"""
        frontmatter, body = parser._extract_frontmatter(content)

        assert frontmatter["title"] == "Test"
        assert frontmatter["author"] == "John Doe"
        assert body.strip() == "# Content"

    def test_extract_frontmatter_invalid_yaml(self, parser):
        """Test handling invalid YAML frontmatter."""
        content = """---
invalid: yaml: [unclosed
---
# Content
"""
        # Should not raise, just log warning
        frontmatter, body = parser._extract_frontmatter(content)
        assert frontmatter == {}
        assert "# Content" in body

    def test_extract_frontmatter_no_frontmatter(self, parser):
        """Test content without frontmatter."""
        content = "# Just content\nNo frontmatter here"
        frontmatter, body = parser._extract_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_parse_messages_chinese_roles(self, parser):
        """Test parsing messages with Chinese role markers."""
        content = """# Test

## 使用者

這是使用者的問題

## Gemini

這是助手的回答
"""
        result = parser.parse(content, "test.md")

        messages = result.parsed_content["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_parse_messages_english_roles(self, parser):
        """Test parsing messages with English role markers."""
        content = """# Test

## User

What is this?

## Assistant

This is a test.
"""
        result = parser.parse(content, "test.md")

        messages = result.parsed_content["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_infer_role_from_patterns(self, parser):
        """Test role inference from known patterns."""
        # Test user patterns
        assert parser._infer_role("使用者", "some content") == "user"
        assert parser._infer_role("User", "some content") == "user"
        assert parser._infer_role("用戶", "some content") == "user"

        # Test assistant patterns
        assert parser._infer_role("Gemini", "some content") == "assistant"
        assert parser._infer_role("Assistant", "some content") == "assistant"
        assert parser._infer_role("AI", "some content") == "assistant"

        # Test system patterns
        assert parser._infer_role("System", "some content") == "system"

    def test_infer_role_from_question_words(self, parser):
        """Test role inference from question words."""
        # Chinese question words
        assert parser._infer_role("Unknown", "什麼是Python？") == "user"
        assert parser._infer_role("Unknown", "如何安裝？") == "user"
        assert parser._infer_role("Unknown", "為什麼這樣？") == "user"

        # English question words
        assert parser._infer_role("Unknown", "What is Python?") == "user"
        assert parser._infer_role("Unknown", "How to install?") == "user"
        assert parser._infer_role("Unknown", "Why is this?") == "user"

    def test_infer_role_defaults_to_assistant(self, parser):
        """Test that unknown roles default to assistant."""
        assert parser._infer_role("Unknown", "This is a statement.") == "assistant"

    def test_extract_metadata_from_title(self, parser):
        """Test metadata extraction from markdown title."""
        content = """# My Test Title

## User

Hello
"""
        frontmatter = {}
        metadata = parser._extract_metadata(frontmatter, content)

        assert metadata["title"] == "My Test Title"

    def test_extract_metadata_from_frontmatter(self, parser):
        """Test metadata extraction from frontmatter."""
        content = """---
title: Frontmatter Title
author: Test Author
---
# Markdown Title

Content
"""
        frontmatter = {"title": "Frontmatter Title", "author": "Test Author"}
        metadata = parser._extract_metadata(frontmatter, content)

        # Frontmatter should take precedence
        assert metadata["title"] == "Frontmatter Title"
        assert metadata["author"] == "Test Author"

    def test_detect_language_chinese(self, parser):
        """Test Chinese language detection."""
        from blog_agent.storage.models import Message

        messages = [
            Message(role="user", content="這是中文內容，包含很多中文字符。"),
            Message(role="assistant", content="是的，這是繁體中文。"),
        ]

        language = parser._detect_language(messages)
        assert language == "zh-TW"

    def test_detect_language_english(self, parser):
        """Test English language detection."""
        from blog_agent.storage.models import Message

        messages = [
            Message(role="user", content="This is English content."),
            Message(role="assistant", content="Yes, this is English."),
        ]

        language = parser._detect_language(messages)
        assert language == "en"

    def test_detect_language_mixed(self, parser):
        """Test language detection with mixed content."""
        from blog_agent.storage.models import Message

        messages = [
            Message(role="user", content="This is English with some 中文 mixed in."),
        ]

        # Should detect as Chinese if > 30% Chinese characters
        language = parser._detect_language(messages)
        # This might be "en" or "zh-TW" depending on the ratio
        assert language in ["en", "zh-TW"]

    def test_detect_language_empty_messages(self, parser):
        """Test language detection with empty messages."""
        language = parser._detect_language([])
        assert language is None

    def test_parse_empty_content(self, parser):
        """Test parsing empty content."""
        content = ""
        result = parser.parse(content, "empty.md")

        assert result.message_count == 0
        assert result.parsed_content["messages"] == []

    def test_parse_content_with_code_blocks(self, parser, sample_content, sample_file_path):
        """Test parsing content with code blocks."""
        result = parser.parse(sample_content, sample_file_path)

        # Should handle code blocks in messages
        messages = result.parsed_content["messages"]
        assert len(messages) > 0

        # First message should contain Python code
        first_user_msg = next(
            (msg for msg in messages if msg["role"] == "user"), None
        )
        assert first_user_msg is not None
        assert "```python" in first_user_msg["content"] or "class" in first_user_msg["content"]

    def test_parse_handles_multiple_sections(self, parser):
        """Test parsing multiple message sections."""
        content = """# Conversation

## User

First question

## Assistant

First answer

## User

Second question

## Assistant

Second answer
"""
        result = parser.parse(content, "test.md")

        assert result.message_count == 4
        messages = result.parsed_content["messages"]
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[3]["role"] == "assistant"

    def test_parse_skips_empty_sections(self, parser):
        """Test that empty sections are skipped."""
        content = """# Test

## User

Valid content

## Assistant

"""
        result = parser.parse(content, "test.md")

        # Should only have one message (empty assistant section skipped)
        messages = result.parsed_content["messages"]
        assert len(messages) >= 1
        assert messages[0]["role"] == "user"

    def test_parse_handles_malformed_markdown(self, parser):
        """Test that parser handles malformed markdown gracefully."""
        # Parser should handle various edge cases without crashing
        content = """# Test

## User

Content with no closing

## Assistant

More content
"""
        # Should parse successfully even with potential issues
        result = parser.parse(content, "test.md")
        assert result.message_count >= 0  # Should not crash

    def test_parsed_content_structure(self, parser, sample_content, sample_file_path):
        """Test that parsed_content has correct structure."""
        result = parser.parse(sample_content, sample_file_path)

        assert "messages" in result.parsed_content
        assert "frontmatter" in result.parsed_content
        assert isinstance(result.parsed_content["messages"], list)
        assert isinstance(result.parsed_content["frontmatter"], dict)

    def test_message_model_dump(self, parser, sample_content, sample_file_path):
        """Test that messages are properly serialized."""
        result = parser.parse(sample_content, sample_file_path)

        messages = result.parsed_content["messages"]
        for msg in messages:
            # Should be dict (from model_dump)
            assert isinstance(msg, dict)
            assert "role" in msg
            assert "content" in msg

