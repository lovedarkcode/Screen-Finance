"""Probe configured FMP coverage without persisting filings or exposing credentials."""
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.services.filings.fmp import FMPClient, PipelineError
from app.config import settings


async def main():
    results = []
    async with httpx.AsyncClient() as client:
        provider = FMPClient(client)
        for symbol in ("AAPL", "MSFT", "RELIANCE.NS", "TATASTEEL.NS"):
            try:
                rows, rejected = await provider.income_statements(symbol)
                results.append({"ticker": symbol, "records": len(rows), "rejected": rejected,
                                "latest": rows[0][0].model_dump(mode="json")})
            except PipelineError as error:
                results.append({"ticker": symbol, "error": error.code})
    output = {"nebius_configured": bool(settings.NEBIUS_API_KEY), "results": results}
    Path(__file__).with_name("fmp-provider-verification.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"results": [{key: row[key] for key in ("ticker", "records", "rejected", "error") if key in row} for row in results]}))


if __name__ == "__main__":
    asyncio.run(main())
