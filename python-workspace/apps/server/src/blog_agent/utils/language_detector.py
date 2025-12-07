"""Language detection utility."""

import re
from typing import Optional

from blog_agent.utils.logging import get_logger

logger = get_logger(__name__)


def detect_language(text: str) -> Optional[str]:
    """Detect language from text using heuristics."""
    if not text:
        return None

    # Count Chinese characters
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total_chars = len(re.findall(r"\S", text))

    if total_chars == 0:
        return None

    chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0

    # If more than 30% Chinese characters, likely Chinese
    if chinese_ratio > 0.3:
        # Try to distinguish Traditional vs Simplified
        # Traditional: 繁體, 簡體: 简体
        if "繁體" in text or "繁體中文" in text:
            return "zh-TW"
        elif "简体" in text or "简体中文" in text:
            return "zh-CN"
        else:
            # Default to Traditional for now
            return "zh-TW"

    # Check for other languages
    # Japanese
    japanese_chars = len(re.findall(r"[\u3040-\u309F\u30A0-\u30FF]", text))
    if japanese_chars > 10:
        return "ja"

    # Korean
    korean_chars = len(re.findall(r"[\uAC00-\uD7AF]", text))
    if korean_chars > 10:
        return "ko"

    # Default to English
    return "en"

