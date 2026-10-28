"""Migrate a hosted database and optionally seed verified public market data.

python scripts/prepare_screener_production.py --env-file .vercel/production.env --seed-local
Credentials are read from the ignored env file and never printed. Accounts and
portfolios are never copied. The scheduled worker maintains data after seeding.
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--seed-local", action="store_true")
    args = parser.parse_args()
    values = dotenv_values(args.env_file)
    destination = values.get("DATABASE_URL_UNPOOLED") or values.get("DATABASE_URL")
    if not destination or "SENSITIVE" in destination:
        parser.error("A usable hosted DATABASE_URL is required")
    target_url = make_url(destination).set(drivername="postgresql+psycopg2")
    if target_url.host in (None, "localhost", "127.0.0.1", "::1"):
        parser.error("The destination must be the hosted production database")
    os.environ.update(DATABASE_URL=destination, DEBUG="false", ENVIRONMENT="production")
    config = Config(str(ROOT / "backend/alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "backend/app/db/migrations"))
    command.upgrade(config, "head")
    print("Hosted schema migrated.", flush=True)
    if not args.seed_local:
        return
    from app.models.stock import Stock
    from app.models.financials import Financials
    from app.models.quarterly_poll_state import QuarterlyPollState

    local = dotenv_values(ROOT / "backend/.env")
    source_url = make_url(local["DATABASE_URL"]).set(drivername="postgresql+psycopg2")
    if (source_url.host, source_url.database) == (target_url.host, target_url.database):
        parser.error("Source and destination must be different databases")
    source = create_engine(source_url, connect_args={"connect_timeout": 15})
    target = create_engine(target_url, connect_args={"connect_timeout": 15})
    try:
        with source.connect().execution_options(isolation_level="REPEATABLE READ") as read, read.begin():
            covered = select(Financials.stock_id).where(Financials.validation_version == 1, Financials.snapshot_key.is_not(None))
            stocks = list(read.execute(select(Stock.__table__).where(Stock.id.in_(covered))).mappings())
            financials = list(read.execute(select(Financials.__table__).where(Financials.stock_id.in_(covered), Financials.snapshot_key.is_not(None))).mappings())
            membership = read.scalar(select(QuarterlyPollState.payload).where(QuarterlyPollState.name == "screener_sp500"))
        with target.begin() as write:
            ids = {}
            for offset in range(0, len(stocks), 250):
                batch = stocks[offset:offset + 250]
                statement = insert(Stock).values([{key: value for key, value in row.items() if key != "id"} for row in batch])
                write.execute(statement.on_conflict_do_update(index_elements=[Stock.symbol],
                    set_={key: getattr(statement.excluded, key) for key in batch[0] if key not in ("id", "symbol")},
                    where=or_(Stock.updated_at.is_(None), statement.excluded.updated_at >= Stock.updated_at)))
                by_symbol = dict(write.execute(select(Stock.symbol, Stock.id).where(Stock.symbol.in_([row["symbol"] for row in batch]))).all())
                ids.update({row["id"]: by_symbol[row["symbol"]] for row in batch})
            for offset in range(0, len(financials), 250):
                batch = [{**{key: value for key, value in row.items() if key not in ("id", "stock_id")}, "stock_id": ids[row["stock_id"]]} for row in financials[offset:offset + 250]]
                statement = insert(Financials).values(batch)
                write.execute(statement.on_conflict_do_update(constraint="uq_financial_snapshot",
                    set_={key: getattr(statement.excluded, key) for key in batch[0] if key not in ("stock_id", "snapshot_key")},
                    where=or_(Financials.updated_at.is_(None), statement.excluded.updated_at >= Financials.updated_at)))
            if membership:
                statement = insert(QuarterlyPollState).values(name="screener_sp500", payload=membership)
                write.execute(statement.on_conflict_do_nothing(index_elements=[QuarterlyPollState.name]))
            print(f"Public data seeded: {len(stocks)} listings, {len(financials)} financial snapshots.", flush=True)
            print(f"Hosted financial coverage: {write.scalar(select(func.count(func.distinct(Financials.stock_id))))} listings.", flush=True)
    finally:
        source.dispose()
        target.dispose()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Production preparation failed: {type(error).__name__}", flush=True)
        raise SystemExit(1) from None
