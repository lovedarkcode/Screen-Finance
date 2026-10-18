"""Read-only readiness check; never prints connection strings or credentials."""
import asyncio
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from sqlalchemy import text
from app.db.session import engine


async def main():
    result = {}
    for package in ["langgraph", "sqlalchemy", "redis", "openai", "aiosqlite"]:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not installed"
    engine.echo = False
    try:
        async with asyncio.timeout(8), engine.connect() as connection:
            tables = (await connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))).scalars().all()
            result["database"] = "connected"
            result["tables"] = tables
            for table in ["stocks", "financials"]:
                if table in tables:
                    result[table + "_count"] = (await connection.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()
    except Exception as error:
        result["database"] = "unavailable: " + type(error).__name__
    finally:
        await engine.dispose()
    print(json.dumps(result))


asyncio.run(main())
