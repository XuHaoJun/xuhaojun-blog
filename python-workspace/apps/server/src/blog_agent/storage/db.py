"""Database connection utilities."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get database connection context manager."""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:test@localhost:5432/blog_agent",
    )
    
    conn = await asyncpg.connect(database_url)
    try:
        yield conn
    finally:
        await conn.close()


async def check_db_connection() -> bool:
    """Check if database connection is available."""
    try:
        async with get_db_connection() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False

