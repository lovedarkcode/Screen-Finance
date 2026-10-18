"""Opt-in live check using backend/.env; never prints credentials or provider bodies.

Run from backend: python ../docs/ai-stock-analysis/live_check.py NVDA AAPL RELIANCE MTARTECH
"""
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from openai import AsyncOpenAI, APIConnectionError, APIError, APIStatusError, APITimeoutError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.services.ai.stock_analysis_service import analyze_stock, _load_financials, _resolve_quote
from app.services.ai.stock_analysis_service import NVIDIA_URL
from app.services.ai.financial_evidence import assess_quality, build_evidence
from app.config import settings


async def main():
    if "--probe" in sys.argv:
        key = settings.NVIDIA_API_KEY.get_secret_value()
        try:
            async with AsyncOpenAI(base_url=NVIDIA_URL.removesuffix("/chat/completions"), api_key=key, max_retries=0, timeout=60) as client:
                stream = await client.chat.completions.create(model=settings.NVIDIA_MODEL, messages=[{"role": "user", "content": "Write a limerick about the wonders of GPU computing."}], temperature=1, top_p=.95, max_tokens=16384, extra_body={"chat_template_kwargs": {"enable_thinking": True}}, stream=True)
                content = []
                async with stream:
                    async for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content.append(chunk.choices[0].delta.content)
                print(json.dumps({"sdk": "OpenAI client targeting NVIDIA", "model": settings.NVIDIA_MODEL, "stream": True, "finalContentCharacters": len("".join(content))}))
                return 0
        except APIStatusError as error:
            print("NVIDIA HTTP", error.status_code)
            message = error.body
            if isinstance(message, dict):
                message = message.get("message", message.get("detail", "Provider returned an error"))
            print(str(message).replace(key, "[redacted]")[:400])
        except (APIConnectionError, APITimeoutError):
            print("NVIDIA connection failed or timed out")
        except APIError as error:
            print("NVIDIA stream error:", str(error.message).replace(key, "[redacted]")[:400])
        return 1
    failed = False
    for symbol in [arg for arg in sys.argv[1:] if not arg.startswith("--")] or ["NVDA"]:
        try:
            if "--evidence" in sys.argv:
                quote = await _resolve_quote(symbol)
                retrieved = datetime.now(UTC)
                snapshot = await run_in_threadpool(_load_financials, quote["symbol"])
                evidence, metric_ids, sources, warnings, trends = build_evidence(quote, snapshot, retrieved)
                quality = assess_quality(evidence, trends, snapshot, retrieved)
                result = {"financialEvidenceOnly": True, "symbol": quote["symbol"], "exchange": quote["exchange"], "retrievedAt": retrieved.isoformat(), "evidenceCount": len(evidence), "quality": quality.model_dump(), "metrics": [item.model_dump(mode="json") for item in evidence if item.id in metric_ids], "trends": [row.model_dump(mode="json") for row in trends]}
                (Path(__file__).parent / f"live-evidence-{quote['symbol']}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
                print(json.dumps({"symbol": quote["symbol"], "financialEvidenceOnly": True, "sourceVerified": len(evidence), "checkedCalculations": quality.checkedCalculations, "annualPeriods": quality.annualPeriods, "quarterlyPeriods": quality.quarterlyPeriods, "issues": [issue.code for issue in quality.issues]}), flush=True)
                continue
            report = await analyze_stock(symbol)
            path = Path(__file__).parent / f"live-{report.symbol}.json"
            path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
            print(json.dumps({"requested": symbol, "symbol": report.symbol, "provider": report.provider, "model": report.model, "evidence": len(report.evidence), "metrics": len(report.metricIds), "verifiedClaims": sum(len(getattr(report.research, key)) for key in ["summary", "strengths", "risks", "watchItems"])}), flush=True)
        except HTTPException as error:
            failed = True
            print(json.dumps({"symbol": symbol, "status": error.status_code, "detail": error.detail}), flush=True)
        except Exception as error:
            failed = True
            print(json.dumps({"symbol": symbol, "errorType": type(error).__name__}), flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
