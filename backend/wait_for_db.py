#!/usr/bin/env python3
"""Wait for PostgreSQL to be ready."""
import asyncio
import os
import sys
import time
from urllib.parse import urlparse

import asyncpg


async def wait_for_db(dsn: str, timeout: int = 60, interval: float = 1.0) -> bool:
    """Wait for PostgreSQL to accept connections."""
    start = time.time()
    parsed = urlparse(dsn)
    
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    user = parsed.username or "postgres"
    password = parsed.password or ""
    database = parsed.path.lstrip("/") or "postgres"
    
    print(f"🔌 Connecting to {host}:{port}/{database} as {user}", flush=True)
    
    while True:
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                ),
                timeout=5.0,
            )
            await conn.close()
            print(f"✅ Database ready at {host}:{port} after {time.time() - start:.0f}s", flush=True)
            return True
        except Exception as e:
            elapsed = time.time() - start
            if elapsed > timeout:
                print(f"❌ Timeout waiting for database after {elapsed:.0f}s: {e}", flush=True)
                return False
            print(f"⏳ Waiting for database... ({elapsed:.0f}s) {type(e).__name__}: {e}", flush=True)
            await asyncio.sleep(interval)


if __name__ == "__main__":
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        print("❌ DATABASE_URL not set", flush=True)
        sys.exit(1)
    
    print(f"🚀 Starting wait_for_db, DSN: {dsn[:50]}...", flush=True)
    
    # Convert asyncpg URL if needed
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    success = asyncio.run(wait_for_db(dsn))
    sys.exit(0 if success else 1)