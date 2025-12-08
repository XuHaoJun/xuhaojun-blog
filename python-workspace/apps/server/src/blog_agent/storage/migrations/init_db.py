#!/usr/bin/env python3
"""Initialize database schema."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from blog_agent.storage.db import get_db_connection


async def init_db():
    """Initialize database with schema."""
    migration_file = Path(__file__).parent / "001_init_schema.sql"
    
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()
    
    async with get_db_connection() as conn:
        # Execute all statements in a transaction
        async with conn.transaction():
            await conn.execute(sql)
        print("✓ Database schema initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_db())

