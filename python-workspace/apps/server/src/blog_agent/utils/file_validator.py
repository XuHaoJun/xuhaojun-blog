"""File validation utilities for conversation logs (FR-029, FR-030)."""

import re
from pathlib import Path
from typing import Optional, Tuple


def validate_conversations_directory(file_path: str, project_root: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate that file path is within conversations/ directory (FR-029).
    
    Args:
        file_path: Path to the file to validate
        project_root: Optional project root directory. If not provided, 
                     will try to infer from file_path.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path).resolve()
    
    # Check if path contains conversations/ directory
    parts = path.parts
    if "conversations" not in parts:
        return False, f"File path must be within conversations/ directory. Got: {file_path}"
    
    # Find the index of conversations in the path
    conversations_idx = parts.index("conversations")
    
    # File should be directly in conversations/ or in a subdirectory
    # But not outside conversations/
    if conversations_idx == len(parts) - 1:
        return False, f"File path points to conversations/ directory itself, not a file. Got: {file_path}"
    
    return True, None


def validate_file_naming_convention(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file naming convention: YYYY-MM-DD_HH-MM-SS_Model_Provider.ext (FR-030).
    
    Expected format:
    - YYYY-MM-DD: Date (4-digit year, 2-digit month, 2-digit day)
    - HH-MM-SS: Time (24-hour format, 2-digit hour, minute, second)
    - Model: AI model name (e.g., Gemini, GPT-4, Claude)
    - Provider: Service provider (e.g., Google_Gemini, OpenAI, Anthropic)
    - ext: File extension (.md, .json, .csv, .txt)
    
    Args:
        file_path: Path to the file to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    filename = Path(file_path).name
    
    # Pattern: YYYY-MM-DD_HH-MM-SS_Model_Provider.ext
    # Example: 2025-12-07_15-30-59_Gemini_Google_Gemini.md
    pattern = r'^(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})_([^_]+)_([^_]+)\.([^.]+)$'
    
    match = re.match(pattern, filename)
    if not match:
        return False, (
            f"File name does not match required format: YYYY-MM-DD_HH-MM-SS_Model_Provider.ext\n"
            f"Got: {filename}\n"
            f"Example: 2025-12-07_15-30-59_Gemini_Google_Gemini.md"
        )
    
    date_part, time_part, model, provider, ext = match.groups()
    
    # Validate date format (basic check - YYYY-MM-DD)
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(date_pattern, date_part):
        return False, f"Invalid date format in filename: {date_part}. Expected YYYY-MM-DD"
    
    # Validate time format (basic check - HH-MM-SS)
    time_pattern = r'^\d{2}-\d{2}-\d{2}$'
    if not re.match(time_pattern, time_part):
        return False, f"Invalid time format in filename: {time_part}. Expected HH-MM-SS"
    
    # Validate extension
    valid_extensions = ['md', 'json', 'csv', 'txt', 'markdown']
    if ext.lower() not in valid_extensions:
        return False, f"Invalid file extension: {ext}. Allowed: {', '.join(valid_extensions)}"
    
    # Validate date values (basic range checks)
    try:
        year, month, day = map(int, date_part.split('-'))
        hour, minute, second = map(int, time_part.split('-'))
        
        if not (1 <= month <= 12):
            return False, f"Invalid month: {month}. Must be 1-12"
        if not (1 <= day <= 31):
            return False, f"Invalid day: {day}. Must be 1-31"
        if not (0 <= hour <= 23):
            return False, f"Invalid hour: {hour}. Must be 0-23"
        if not (0 <= minute <= 59):
            return False, f"Invalid minute: {minute}. Must be 0-59"
        if not (0 <= second <= 59):
            return False, f"Invalid second: {second}. Must be 0-59"
    except ValueError:
        return False, f"Invalid numeric values in date/time: {date_part} {time_part}"
    
    return True, None


def validate_file_path(file_path: str, project_root: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate both directory structure and naming convention.
    
    Args:
        file_path: Path to the file to validate
        project_root: Optional project root directory
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check directory structure
    dir_valid, dir_error = validate_conversations_directory(file_path, project_root)
    if not dir_valid:
        return False, dir_error
    
    # Check naming convention
    name_valid, name_error = validate_file_naming_convention(file_path)
    if not name_valid:
        return False, name_error
    
    return True, None

