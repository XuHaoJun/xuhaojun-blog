#!/usr/bin/env python3
"""Initialize database schema and run all migrations."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from blog_agent.storage.db import get_db_connection


async def init_db():
    """Initialize database with all migrations."""
    migrations_dir = Path(__file__).parent
    
    # Get all migration files in order
    migration_files = sorted([
        f for f in migrations_dir.glob("*.sql")
        if f.name.startswith(("001_", "002_", "003_", "004_"))
    ])
    
    if not migration_files:
        print("No migration files found")
        return
    
    async with get_db_connection() as conn:
        # Check which migrations have already been applied
        applied_migrations = set()
        try:
            rows = await conn.fetch("SELECT migration_name FROM migration_history")
            applied_migrations = {row["migration_name"] for row in rows}
            print(f"Found {len(applied_migrations)} already applied migration(s)")
        except Exception as e:
            # migration_history table doesn't exist yet, will be created by first migration
            print("Migration history table not found, will be created by first migration")
        
        async with conn.transaction():
            for migration_file in migration_files:
                migration_name = migration_file.name
                
                if migration_name in applied_migrations:
                    print(f"⏭️  Skipping already applied migration: {migration_name}")
                    continue
                
                print(f"▶️  Running migration: {migration_name}")
                with open(migration_file, "r", encoding="utf-8") as f:
                    sql = f.read()
                await conn.execute(sql)
                
                # Record that this migration was applied
                # Use ON CONFLICT DO NOTHING in case migration_history table was just created
                try:
                    await conn.execute(
                        "INSERT INTO migration_history (migration_name) VALUES ($1) ON CONFLICT (migration_name) DO NOTHING",
                        migration_name
                    )
                except Exception as e:
                    # If migration_history table doesn't exist yet (for 001), that's okay
                    # It will be created by the migration itself
                    if "migration_history" not in str(e).lower():
                        raise
    
    print("✓ All database migrations applied successfully")


if __name__ == "__main__":
    asyncio.run(init_db())

