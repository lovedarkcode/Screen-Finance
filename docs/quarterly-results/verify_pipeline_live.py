"""Check real DB/API state and Nebius model access without creating synthetic filings."""
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
from openai import APIError, APIStatusError, AsyncOpenAI, DefaultAsyncHttpxClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.config import settings
from app.db.session import engine
from app.db.session import SessionLocal
from app.models.quarterly_result import QuarterlyResult
from app.services.filings.yahoo import PROVIDER
from sqlalchemy import func, select
from app.dependencies import require_user
from app.main import app


async def main():
    engine.echo = False
    output = {"checked_at": datetime.now(UTC).isoformat(), "authentication": "isolated in-process override; deployed authentication unchanged"}
    app.dependency_overrides[require_user] = lambda: object()
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://isolated-app") as client:
            output["api"] = {}
            for path in ("/api/results", "/api/v1/results", "/api/results/latest", "/api/results/AAPL", "/api/v1/results/latest",
                         "/api/results/latest?market=IN&exchange=NSE&page_size=12", "/api/results/latest?market=IN&exchange=BSE&page_size=12",
                         "/api/results/latest?exchange=NYSE&page_size=12", "/api/results/latest?exchange=NASDAQ&page_size=12"):
                response = await client.get(path)
                output["api"][path] = {"status": response.status_code, "body": response.json()}
        async with SessionLocal() as session:
            quarters, companies = (await session.execute(select(func.count(), func.count(func.distinct(QuarterlyResult.company_id)))
                .where(QuarterlyResult.provider == PROVIDER))).one()
            summaries = dict((await session.execute(select(QuarterlyResult.summary_status, func.count()).where(QuarterlyResult.provider == PROVIDER)
                                                    .group_by(QuarterlyResult.summary_status))).all())
            output["financial_storage"] = {"provider": PROVIDER, "quarters": quarters, "companies": companies, "summary_status": summaries}
    finally:
        app.dependency_overrides.pop(require_user, None)
        await engine.dispose()
    if settings.NEBIUS_API_KEY:
        try:
            async with AsyncOpenAI(base_url=settings.NEBIUS_BASE_URL, api_key=settings.NEBIUS_API_KEY.get_secret_value(),
                                  http_client=DefaultAsyncHttpxClient(follow_redirects=False), timeout=20, max_retries=0) as client:
                models = await client.models.list()
                output["nebius"] = {"status": "reachable", "model": settings.NEBIUS_MODEL, "model_listed": any(item.id == settings.NEBIUS_MODEL for item in models.data)}
        except APIStatusError as error:
            output["nebius"] = {"http_status": error.status_code}
        except APIError:
            output["nebius"] = {"status": "connection_failed"}
    else:
        output["nebius"] = {"status": "key_missing"}
    Path(__file__).with_name("pipeline-live-verification.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"api": {path: result["status"] for path, result in output["api"].items()}, "financial_storage": output["financial_storage"], "nebius": output["nebius"]}))


if __name__ == "__main__":
    asyncio.run(main())
