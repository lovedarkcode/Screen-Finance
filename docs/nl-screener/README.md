# Natural Language Stock Screener

The header's **AI Screener** button opens the bot near the top of `/feed`, the existing authenticated landing page, using `/feed?screener=ai`. The default feed keeps the bot hidden. Clicking the button again closes it; browser history and direct links preserve the open/closed view. Opening the bot scrolls to it and focuses its query input. It interprets Indian/US financial screening requests, shows editable conditions, executes PostgreSQL filters, and links results to `/stock/:symbol` and its existing Analyze with AI button. Existing market overview, charts, sector discovery and stock analysis remain in place.

## Architecture and files

The existing stack is React/Vite, ChaiUI, Axios, FastAPI, SQLAlchemy/asyncpg, PostgreSQL, Redis, Celery and NVIDIA's API. The current PostgreSQL dataset has 16 stocks and 173 financial records. See [COVERAGE_FIX.md](COVERAGE_FIX.md) for the latest investigation, fixes, SQL/API parity checks and coverage limits.

New implementation:

- `frontend/src/components/screener/NaturalLanguageScreener.jsx` and `natural-language-screener.css`: feed bot, examples, loading/errors/clarification, editable filters, financial table, server-side sorting/pagination and stock links.
- `backend/app/services/screener/metrics.py`: supported metric/operator/period registry and definitions.
- `parser.py`: NVIDIA-only structured filter extraction, with copied source conditions and bounded streaming.
- `validator.py`: units, threshold/source checks, operators, markets, dates, sectors, missing conditions, unsupported requests and contradictions.
- `query_builder.py`: parameterized SQLAlchemy SELECTs, the latest eligible value independently for each metric, exact fiscal dates, and observation-date cutoffs.
- `ingestion.py`: real Yahoo/yfinance refresh through the existing financial evidence engine, with source metadata.
- `cache.py`: versioned parsing caches plus rate limits, using existing Redis with bounded local fallbacks.
- `backend/app/agents/screener/graph.py`: compiled, four-node parse → validate → execute → format LangGraph workflow, with clarification/unsupported/invalid short-circuits and no autonomous loops.
- Migration `a31f70d293c1_screener_metrics.py`: additive fields/indexes on existing tables; no duplicate financial database or vector store.
- `scripts/refresh_screener.py`: import/refresh the real stock universe.
- `backend/app/tests/test_nl_screener.py`: clearly identified deterministic mixed-market fixtures.
- `docs/nl-screener/verify.cjs`, `check_environment.py`, `live_check.py`: browser/readiness/live verification.

Modified integration files: `HomePage.jsx`, `screener.service.js`, backend `models/stock.py`, `models/financials.py`, `schemas/screener.py`, `api/v1/screener.py`, and `workers/stock_sync_worker.py`.

## Data setup

No new dependency is required. Existing `DATABASE_URL`, `NVIDIA_API_KEY`, `NVIDIA_MODEL`, and optional `REDIS_URL` are used. Optional `NVIDIA_SCREENER_MODEL` selects a separate feed model; when omitted it falls back to `NVIDIA_MODEL`. Following user approval, the local configuration sets `NVIDIA_SCREENER_MODEL=nvidia/nemotron-3-super-120b-a12b`. The stock-analysis model setting remains unchanged. NVIDIA is the only LLM endpoint; `OPENAI_API_KEY` is never used. Basic numeric screening never uses Qdrant.

From `backend`, with the existing Python environment activated:

```powershell
$env:DEBUG = 'false' # only needed if an inherited DEBUG value is incompatible
python -m alembic upgrade head
python ../scripts/refresh_screener.py
uvicorn app.main:app --reload
```

The default import is a documented starter universe of sixteen real US/Indian tickers. This is not an exchange-wide dataset. Add your own symbols without editing code:

```powershell
python ../scripts/refresh_screener.py AAPL NVDA BE RELIANCE.NS MTARTECH.NS
python ../scripts/refresh_screener.py --symbols-file ../symbols.txt
```

Each symbol is committed atomically after evidence verification. Raw existing financial columns are reused where applicable; derived metrics, fiscal ends, currencies, validation version and provenance extend the existing financial rows. Unverified financial values are excluded from financial filters, with an explanation when they prevent matches; their stock-master records remain eligible for unfiltered searches. Nulls remain null. A refresh clears missing values in refreshed snapshots and invalidates missing latest TTM/balance snapshots. Result rows are read on every execution, so corrections become visible even if their timestamps were not updated. Observation timestamps and validation metadata must remain accurate for historical screening.

The existing Celery tasks `workers.stock_sync.sync_symbol` and `workers.stock_sync.sync_all` now invoke this same real refresh. No recurring schedule is enabled automatically. Run the refresh periodically as appropriate for the imported universe and provider limits.

## Endpoints

All search/execute calls require the existing user Bearer token and are limited to twenty screening requests per user per minute. Metrics are public definitions; sectors are public financial taxonomy.

- `POST /api/v1/screener/search`: `{"query":"Find US technology companies with ROE above 20% and debt-to-equity below 0.5.","page":1}`
- `POST /api/v1/screener/execute`: `{"screen":{"market":"US","filters":[{"field":"roe","operator":"gt","value":20,"period":"annual"}],"sort_by":"market_cap","limit":25},"page":1}`. Edited filters, sorting and pagination use this endpoint and make no LLM call.
- `GET /api/v1/screener/metrics`: field names, definitions, units, supported periods and operators.
- `GET /api/v1/screener/sectors`: available imported market/sector and market/industry combinations.
- Legacy `POST /screener/run` routes to the new search flow. Legacy `/save` is authenticated and returns an explicit not-implemented response rather than claiming to save data.

Responses contain `status`, `parsed_filters`, `stocks`, `total_count`, `page`, `page_size`, `universe_count`, `data_as_of`, `warnings`, `execution_ms` and `cached`. Non-executable statuses are `clarification`, `unsupported`, and `invalid`, with a meaningful `clarification` message and no results. Provider/database failures use safe HTTP errors; no secret, raw provider body or stack trace is returned.

`original_query` contains the submitted search prompt. Structured `/execute` accepts optional `original_query` for context without reparsing edited filters; omission returns null. `universe_count` counts all imported stocks in the selected market, including companies without financials, before other filters and pagination. Null/omitted market means all markets. `empty_reason` and `explanation` distinguish empty universes, no matches, missing metrics, unavailable periods, incompatible currencies and out-of-range pages. Null `period_end` means latest available reporting period, never the screening date. Exact fiscal dates are preserved only when requested; unrequested AI-generated dates are removed with a warning.

Result metric keys include their basis, such as `roe:annual`, `roe:ttm`, or `roe:annual:2024-12-31`. Each value includes currency/unit, fiscal period/end, retrieval timestamp, source, definition and validation status. Provider ratios with unknown TTM ends are labeled explicitly and cannot satisfy an exact-date condition. Headline trailing EPS/P/E conflicts are omitted from imported metrics.

An optional `as_of` screening date limits values to observations stored by the end of that UTC date. It is distinct from an exact fiscal `period_end`. Current quote values are unavailable for historical dates if their stored observation is newer. Overwritten provider snapshots cannot be reconstructed; no historical values or dates are fabricated.

## Supported semantics and accuracy

Seventeen metrics are supported: market capitalization, P/E, ROE, annual revenue growth, net/operating margins, debt/equity, current ratio, total/net debt, operating/free cash flow, FCF margin, revenue, net/operating income and trailing EPS. Only reliable available bases are allowed per metric. Annual ROE is recomputed from annual profit and average positive opening/closing equity; provider TTM ROE is a labeled unit conversion, preserving the analysis engine's distinction.

Percent metrics use percentage points. Debt/equity and current ratio use ratios. Monetary thresholds are interpreted as INR for India or USD for US listings unless explicitly specified; incompatible reporting currencies are excluded, with no implicit FX conversion. Zero monetary sign checks, such as net income > 0, can safely include ADR statements in another reporting currency. Monetary sorting groups values by currency and keeps missing values last, without removing companies. Across all markets, nonzero monetary filters need an explicit currency or a selected market.

AND conditions only. Unsupported OR, multi-year consistency/CAGR, ROCE/ROA and other unavailable metrics produce clarification/unsupported feedback. Vague terms such as low debt, cheap or fundamentally strong never receive invented thresholds. The parser must preserve source clauses, numeric thresholds, comparison operators, dates, known metric mentions and explicit sort instructions; uncovered numbers or conditions are rejected. Natural-language interpretation is still a bounded model capability, so the extracted filters remain visible for user review.

The query builder never receives executable SQL from NVIDIA. Identifier/operator mappings are allowlisted and values are bound parameters. Screening uses a separate read-only transaction with a five-second PostgreSQL statement timeout, public stock/financial tables only, deterministic tie sorting, max twelve conditions, max one hundred rows/page and max page one thousand. A dedicated database read-only role may further restrict deployments; the existing application role also supports user/account writes elsewhere.

## Cache, reliability and tests

Parse keys include parser/schema version, configured model and request text. Results are not cached: count/max-timestamp revisions cannot reliably detect in-place corrections. Every execution uses a repeatable-read, read-only PostgreSQL transaction so counts and page rows share one snapshot. Redis caches are optional; local fallbacks are bounded to 256 entries and shared rate limiting falls back to a per-worker limit if Redis is unavailable. Provider errors do not fabricate results. The manual filter editor remains usable without NVIDIA.

```powershell
# From backend
python -m pytest app/tests/test_screener_coverage.py app/tests/test_nl_screener.py app/tests/test_stock_analysis.py app/tests/test_financial_evidence.py app/tests/test_ai.py app/tests/test_stock_detail.py app/tests/test_us_stocks.py app/tests/test_stocks.py app/tests/test_config.py -q
python ../scripts/diagnose_screener.py
python ../docs/nl-screener/verify_coverage.py --ai
python ../docs/nl-screener/check_environment.py
python ../docs/nl-screener/live_check.py --no-ai
python ../docs/nl-screener/live_check.py
# From repository root, with Vite running
$env:APP_URL = 'http://127.0.0.1:5175'
node docs/nl-screener/verify.cjs
```

Automated database tests use an explicitly synthetic SQLite fixture with the same SQLAlchemy query builder, plus PostgreSQL query compilation. Automated NVIDIA tests use a mocked transport. Browser fixtures are isolated and do not touch accounts or databases. The live check uses real configured PostgreSQL/NVIDIA with an in-process authentication override only; deployed authentication is untouched. Public live response artifacts are stored separately from fixture verification.

The additive migration SQL was checked offline, then applied to the configured PostgreSQL database. All sixteen starter listings refreshed successfully (eight US, eight Indian), producing 173 financial snapshots. Live manual screens with positive annual ROE returned six US and eight Indian companies. With the approved Super configuration, the natural-language US technology/ROE/debt query returned two matches; the Indian growth/P/E query returned zero matches; the profitable US companies/market-cap query returned six matches. All returned HTTP 200. Each returned row was checked against its extracted numeric conditions, market, sector/exchange and any explicit currency/date. The earlier Ultra provider checks returned HTTP 503; no substitute financial results were produced. Public responses and model details are recorded in `live-verification-configured.json` and its associated response files.

The empty-result investigation and development-only diagnostics are documented in [DEBUGGING.md](DEBUGGING.md), including the database findings, exact changed files and regression results. The build retains its existing large-bundle warning. Verification artifacts distinguish isolated fixture checks from the real PostgreSQL/NVIDIA checks.

Deferred: saved screens/history; OR/exclusion logic; unsupported financial ratios/CAGR/multi-year predicates; automatic exchange-wide master-list discovery; FX conversion. Imported-universe coverage and fiscal/source metadata are visible so these limits do not become invented matches.
