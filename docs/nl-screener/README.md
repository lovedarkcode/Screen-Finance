# Natural-language stock discovery

The AI Screener opens at `/feed?screener=ai`. Choose **Indian market** or **US market**, type a request, and select **Find stocks**. There is no manual financial-filter editor. Read-only chips show interpreted conditions; the results support server-side sorting and pagination without another model call.

## Coverage and refresh

The former refresh only loaded sixteen starter symbols. The screener now reuses the exchange catalog in `stocks` / `result_listings`, covering NSE, BSE, NYSE and NASDAQ. Discovery has no hardcoded symbol allowlist. Financials are still verified through `services/screener/ingestion.py` and the shared financial-evidence engine. The AI only extracts conditions; it never generates stock matches or financial figures.

`services/screener/universe.py` walks all active catalog listings in fair exchange batches. Separate `screener_checked_at`, `screener_next_check_at`, and `screener_error` columns persist progress independently of quarterly-results ingestion. Each successful listing commits immediately. Successful entries become due after `RESULTS_REFRESH_HOURS`; failures retry after six hours. Provider 429 responses stop the batch. The worker takes a database lease to prevent overlapping CLI/Celery runs, and refreshes the exchange directory daily.

From `backend` after activating the environment:

```powershell
python -m alembic upgrade head
python -m app.workers.stock_sync_worker
# One batch, suitable for cron:
python -m app.workers.stock_sync_worker --once
# Optional India-only fill:
python ../scripts/refresh_screener.py --watch --market IN
# Explicit symbol refresh remains supported:
python ../scripts/refresh_screener.py AAPL RELIANCE.NS
```

From the repository root, `scripts/screener_worker.ps1` starts a hidden Windows worker, with local logs and process identity under `backend/.screener-worker.*`. Use `-Stop` to stop that specific process. Docker Compose includes a continuously running `screener-worker`. Apply migrations before starting it.

Full financial coverage is gradual and depends on provider availability. A listed company with missing required financial values cannot satisfy a numeric filter. The UI shows `universe_count` (catalog listings in the market), `eligible_count` (listings in the requested scope with eligible data for every requested metric), and `total_count` (all matches before pagination). NSE and BSE can contain separate listings for the same company; counts are explicitly labeled as listings.

## Market and index semantics

`POST /api/v1/screener/search` accepts `{"query":"Show companies with revenue growth above 5% and P/E below 25.","market":"IN"}`. The selected market is applied by the server even if the model omits it. A prompt naming a conflicting market requests clarification. Legacy API clients can omit the selector to use market coverage explicitly requested in their prompt.

Requests may specify NSE, BSE, NYSE, NASDAQ or exchange alternatives. An S&P 500 prompt produces `index: "SP500"` and market `US`; it is an index membership restriction, never an exchange alias. The worker refreshes current membership daily using the [FMP constituent endpoint](https://site.financialmodelingprep.com/developer/docs/stable/sp-500) with a [public DataHub constituent list](https://github.com/datasets/s-and-p-500-companies) fallback when FMP is unavailable. Membership older than seven days, missing membership, and historical membership requests produce explicit feedback. Failed downloads do not replace the last good snapshot.

`POST /api/v1/screener/execute` accepts the returned `screen`, `page` and optional `original_query`. Sorting and pagination preserve market, exchanges, index and numeric conditions. `GET /api/v1/screener/metrics` supplies definitions; the existing `/sectors` endpoint remains compatible with API clients.

## Accuracy and limits

Supported metrics and fiscal periods are defined in `services/screener/metrics.py`. The parser supplies copied source clauses. The validator checks operators, thresholds, units, currencies, dates, market, exchanges, index and unsupported conditions before parameterized SQLAlchemy queries run. Results use the latest eligible period independently for each requested metric. Missing values are not zero; nonpositive-earnings P/E values do not qualify as cheap valuations. No foreign-exchange conversions or invented thresholds are applied.

Numeric conditions use AND. Financial OR, unsupported metrics, multi-year consistency and ambiguous descriptions require clarification. Screens are authenticated and rate limited. SQL reads use repeatable-read, read-only transactions with a five-second statement timeout. Parsing is cached with the selected market in the key; results are freshly read on every request. Page size remains bounded to 100, with every matching listing reachable through pagination.

## Verification

```powershell
# From backend (isolated synthetic fixtures, no provider calls):
python -m pytest app/tests/test_screener_universe.py app/tests/test_nl_screener.py app/tests/test_screener_coverage.py app/tests/test_yahoo_results.py -q
# Read-only real coverage and numeric example:
python ../docs/nl-screener/verify_discovery_live.py
# Add live AI prompt verification; refresh-index writes the current membership snapshot:
python ../docs/nl-screener/verify_discovery_live.py --ai --refresh-index
# From root with Vite at port 5175 (isolated browser responses):
node docs/nl-screener/verify.cjs
```

Browser checks cover market selection, query payloads, read-only interpreted conditions, sorting, pagination, result reset, errors, clarification, and desktop/mobile layouts. The fixtures and screenshots are explicitly synthetic. `COVERAGE_FIX.md`, `DEBUGGING.md`, and older live JSON artifacts document earlier investigations and their dataset sizes, not current coverage.
