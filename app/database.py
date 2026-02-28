import asyncpg
import os
import json
import asyncio
import logging
from datetime import datetime

_pool = None
logger = logging.getLogger(__name__)

async def init_db():
    global _pool
    max_retries = 5
    for i in range(max_retries):
        try:
            _pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ratesentry"),
                min_size=2, max_size=10
            )
            break
        except Exception as e:
            if i == max_retries - 1:
                raise e
            logger.warning(f"Database not ready, retrying in 2s... ({i+1}/{max_retries})")
            await asyncio.sleep(2)

    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS policy_audit_log (
                id SERIAL PRIMARY KEY,
                loaded_at TIMESTAMPTZ DEFAULT NOW(),
                policy_name TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                config JSONB NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_policy_audit_name
                ON policy_audit_log(policy_name);
        """)

async def log_policy_load(policies):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        for policy in policies:
            await conn.execute("""
                INSERT INTO policy_audit_log (policy_name, algorithm, config)
                VALUES ($1, $2, $3)
            """, policy.name, policy.algorithm.value, json.dumps(policy.dict()))
