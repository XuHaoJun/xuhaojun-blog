"""Hash calculation utilities for file change detection (FR-031)."""

import hashlib
from typing import Union


def calculate_sha256_hash(content: Union[str, bytes]) -> str:
    """
    Calculate SHA-256 hash of content (FR-031).
    
    Args:
        content: Content to hash (string or bytes)
    
    Returns:
        Hexadecimal string representation of SHA-256 hash
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    hash_obj = hashlib.sha256(content)
    return hash_obj.hexdigest()


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of file content.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hexadecimal string representation of SHA-256 hash
    
    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read
    """
    with open(file_path, 'rb') as f:
        content = f.read()
    
    return calculate_sha256_hash(content)

