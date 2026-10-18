"""Read-only PostgreSQL/SQLAlchemy/FastAPI parity checks; --ai also calls NVIDIA.

Authentication is overridden only in this isolated process. No production data is written.
"""
import argparse
import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import httpx
from sqlalchemy import exists, func, select, text
from app.main import app
from app.dependencies import require_user
from app.db.session import SessionLocal, engine
from app.models.stock import Stock
from app.models.financials import Financials
from app.schemas.screener import ScreenDefinition
from app.services.screener.validator import validate_screen
from app.services.screener.query_builder import statements, diagnostics
from scripts.diagnose_screener import collect

# These identifiers are constants, never model/user input.
FIELDS = {"roe": ("roe", "annual"), "revenue_growth": ("revenue_growth", "annual"), "pe": ("pe", "ttm"), "debt_to_equity": ("debt_to_equity", "snapshot"), "net_profit_margin": ("net_profit_margin", "annual")}
OPS = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<=", "eq": "="}


def direct_sql(screen):
    params = {"today": datetime.now(UTC).date()}
    columns = []
    for field, (column, basis) in FIELDS.items():
        columns.append(f"""(SELECT f.{column} FROM financials f WHERE f.stock_id=s.id
            AND lower(trim(f.period_type))='{basis}' AND f.validation_version=1
            AND f.{column} IS NOT NULL
            AND f.provenance->'{field}'->>'validation_status' IN ('provider','normalized','recomputed')
            AND (f.period_end IS NULL OR f.period_end<=:today)
            AND (f.provenance->'{field}'->>'period_end' IS NULL OR f.provenance->'{field}'->>'period_end'<=CAST(:today AS text))
            ORDER BY f.provenance->'{field}'->>'period_end' DESC NULLS LAST,
            f.period_end DESC NULLS LAST, f.updated_at DESC NULLS LAST, f.id DESC LIMIT 1) AS {field}""")
    predicates = []
    if screen.market:
        predicates.append("country=:market")
        params["market"] = screen.market
    if screen.exchanges or screen.exchange:
        choices = screen.exchanges or [screen.exchange]
        predicates.append("exchange IN (" + ",".join(f":exchange_{i}" for i in range(len(choices))) + ")")
        params.update({f"exchange_{i}": value for i, value in enumerate(choices)})
    for i, condition in enumerate(screen.filters):
        assert condition.field in FIELDS and condition.period == FIELDS[condition.field][1]
        assert not condition.period_end and not condition.currency
        predicates.append(f"{condition.field} {OPS[condition.operator]} :value_{i}")
        params[f"value_{i}"] = condition.value
        if condition.field == 'pe':
            predicates.append("pe>0")
            # Validate the same selected P/E row's earnings domain independently.
            predicates.append("""COALESCE((SELECT f.eps>0 FROM financials f WHERE f.stock_id=candidates.id
                AND f.period_type='ttm' AND f.pe IS NOT NULL AND f.validation_version=1
                AND f.provenance->'pe'->>'validation_status' IN ('provider','normalized','recomputed')
                AND (f.period_end IS NULL OR f.period_end<=:today)
                ORDER BY f.provenance->'pe'->>'period_end' DESC NULLS LAST, f.period_end DESC NULLS LAST,
                f.updated_at DESC NULLS LAST, f.id DESC LIMIT 1), TRUE)""")
    return "WITH candidates AS (SELECT s.*, " + ",".join(columns) + " FROM stocks s) SELECT symbol FROM candidates" + (" WHERE " + " AND ".join(predicates) if predicates else "") + " ORDER BY symbol", params


async def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('--ai', action='store_true')
    args = arguments.parse_args()
    engine.echo = False
    app.dependency_overrides[require_user] = lambda: SimpleNamespace(id=-881)
    report = {"isolated_authentication": True, "financial_data_modified": False, "checks": []}
    cases = [
        ("all", {}), ("India", {"market": "IN"}), ("US", {"market": "US"}),
        ("NSE/BSE", {"market": "IN", "exchanges": ["NSE", "BSE"]}),
        ("BSE", {"market": "IN", "exchange": "BSE"}),
        ("Indian ROE > 0", {"market": "IN", "filters": [{"field": "roe", "operator": "gt", "value": 0}]}),
        ("US ROE > 0", {"market": "US", "filters": [{"field": "roe", "operator": "gt", "value": 0}]}),
        ("five conditions", {"market": "IN", "exchanges": ["NSE", "BSE"], "filters": [
            {"field": field, "operator": op, "value": value} for field, op, value in [("roe", "gt", 15), ("debt_to_equity", "lt", 1), ("revenue_growth", "gt", 10), ("net_profit_margin", "gt", 0), ("pe", "lt", 30)]]}),
        ("growth > 5 and PE < 25", {"market": "IN", "filters": [{"field": "revenue_growth", "operator": "gt", "value": 5}, {"field": "pe", "operator": "lt", "value": 25}]}),
    ]
    try:
        async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://isolated-app', timeout=75) as client:
            async with SessionLocal() as session:
                await session.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
                report['diagnostics'] = await collect(session, validate_screen(ScreenDefinition())[0])
                linked_sql = (await session.execute(text('SELECT count(*) FROM stocks s WHERE EXISTS (SELECT 1 FROM financials f WHERE f.stock_id=s.id)'))).scalar_one()
                linked_orm = (await session.execute(select(func.count(Stock.id)).where(exists(select(Financials.id).where(Financials.stock_id == Stock.id))))).scalar_one()
                assert linked_sql == linked_orm
                report['linked_financials'] = {'sql': linked_sql, 'sqlalchemy': linked_orm}
                for label, payload in cases:
                    screen, _ = validate_screen(ScreenDefinition(**payload, limit=100))
                    sql, params = direct_sql(screen)
                    direct = (await session.execute(text(sql), params)).scalars().all()
                    statement, count, _ = statements(screen, 1)
                    orm_count = (await session.execute(count)).scalar_one()
                    orm_symbols = sorted(row[0].symbol for row in (await session.execute(statement)).all())
                    response = await client.post('/api/v1/screener/execute', json={'screen': screen.model_dump(mode='json')})
                    assert response.status_code == 200, (label, response.status_code)
                    data = response.json()
                    assert data['status'] == 'success'
                    assert data['total_count'] == orm_count == len(direct)
                    assert sorted(row['symbol'] for row in data['stocks']) == orm_symbols == direct
                    check = {'case': label, 'sql_count': len(direct), 'sqlalchemy_count': orm_count, 'api_count': data['total_count'], 'symbols': direct, 'empty_reason': data['empty_reason'], 'explanation': data['explanation'], 'sql': sql, 'parameters': params}
                    if not direct:
                        check['filter_trace'] = await diagnostics(session, screen)
                    report['checks'].append(check)
                    print(json.dumps({k:v for k,v in check.items() if k not in ('sql','parameters','filter_trace')},default=str), flush=True)
            if args.ai:
                queries = [
                    ('Show all available companies without financial filters.', 'all'),
                    ('Show all Indian companies.', 'India'),
                    ('Show Indian companies with ROE above 0%.', 'Indian ROE > 0'),
                    ('Find Indian companies listed on NSE or BSE with ROE greater than 15%, debt-to-equity below 1, annual revenue growth above 10%, positive net profit margin, and P/E below 30.', 'five conditions'),
                ]
                report['natural_language'] = []
                for query, case in queries:
                    response = await client.post('/api/v1/screener/search', json={'query': query})
                    data = response.json()
                    check = {'query': query, 'http': response.status_code, 'status': data.get('status'), 'total_count': data.get('total_count'), 'parsed_filters': data.get('parsed_filters'), 'explanation': data.get('explanation'), 'clarification': data.get('clarification')}
                    report['natural_language'].append(check)
                    print(json.dumps(check),flush=True)
                    expected = next(item for item in report['checks'] if item['case'] == case)
                    assert response.status_code == 200 and data['status'] == 'success', check
                    assert data['total_count'] == expected['api_count']
                    assert sorted(row['symbol'] for row in data['stocks']) == expected['symbols']
    finally:
        app.dependency_overrides.pop(require_user, None)
        await engine.dispose()
        (Path(__file__).parent / 'coverage-verification.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')


if __name__ == '__main__':
    asyncio.run(main())
