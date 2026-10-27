"""Import real validated data; no synthetic financial values or LLM calls.

From backend: python ../scripts/refresh_screener.py [AAPL RELIANCE.NS ...]
No symbols refreshes a resumable exchange-wide batch. --symbols-file accepts one symbol per line.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db.session import engine
from app.services.screener.ingestion import sync_symbol


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbols", nargs="*")
    parser.add_argument("--symbols-file", type=Path)
    parser.add_argument("--market", choices=["IN", "US"], help="Market for exchange-wide discovery")
    parser.add_argument("--watch", action="store_true", help="Continuously fill and refresh the exchange-wide dataset")
    arguments = parser.parse_args()
    symbols = arguments.symbols
    if arguments.symbols_file:
        symbols += [line.strip() for line in arguments.symbols_file.read_text().splitlines() if line.strip() and not line.startswith("#")]
    failed = False
    engine.echo = False
    if not symbols:
        from app.workers.stock_sync_worker import run
        return await run(once=not arguments.watch, market=arguments.market)
    if arguments.watch or arguments.market:
        parser.error("--watch and --market apply to exchange-wide refreshes; omit explicit symbols")
    for symbol in dict.fromkeys(symbols):
        try:
            result = await sync_symbol(symbol)
        except Exception as error:
            failed = True
            result = {"symbol": symbol, "status": "failed", "error_type": type(error).__name__}
        print(json.dumps(result), flush=True)
    await engine.dispose()
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
