# Exchange-wide Yahoo quarterly results

`/results` and `/results/latest` now use **Yahoo Finance/yfinance**. The old eight Indian companies came from the sixteen-symbol screener seed, not a Yahoo eight-stock limit. The default worker no longer calls FMP. Its existing 402 adapter and historical evidence remain available separately.

## Exchange universe and coverage

The configured database was migrated and the public directories imported on 20 October 2026:

| Exchange | Active imported listings | Directory |
| --- | ---: | --- |
| NSE | 3,200 | Main-board and SME CSV files |
| BSE | 4,960 | Active equity directory, excluding mutual-fund ISINs beginning INF |
| NYSE | 2,811 | Nasdaq Trader other-listed directory, exchange N, excluding ETFs/test issues |
| Nasdaq | 4,327 | Nasdaq-listed directory, excluding ETFs/test issues |

These are **listing counts, not companies with successfully downloaded statements**. NSE/BSE listings remain separate with ISINs preserved. Inactive/suspended securities are outside this active-directory universe. US directories also include share classes and other non-ETF securities for which Yahoo may have no statements. Each directory refreshes daily. Updates commit per exchange; failed, malformed or suspiciously small downloads preserve the last successful membership.

Sources: [NSE securities available for trading](https://www.nseindia.com/static/market-data/securities-available-for-trading), [NSE main-board CSV](https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv), [NSE SME CSV](https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv), [BSE active equity directory](https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active), and [Nasdaq directory definitions](https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs).

Yahoo expects `RELIANCE.NS` and BSE security IDs such as `RELIANCE.BO`. Live checks returned no quarterly statements for numeric `500325.BO`; numeric scrip codes remain catalog metadata. US class/preferred-share notation is translated to Yahoo symbols.

The API lists the **entire imported active catalog** immediately. Missing statements have `latest_result: null` and an explicit pending, unavailable or error state. Initial discovery takes hours or longer depending on provider availability. The UI reports real coverage, search, exchange/status/market filters and server pagination. Missing reports never receive invented figures.

## Setup and background operation

Preserve the existing `backend/.env`. See [the complete example](../../backend/.env.example). From `backend/`, with its virtual environment activated:

```powershell
$env:DEBUG = 'false'
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.workers.quarterly_results_worker --bootstrap
```

`--bootstrap` continues paced batches while unchecked listings remain, then switches to the 15-minute schedule. Without it, one bounded batch runs every 15 minutes. `--once` performs one batch for cron. Provider ingestion never runs inside a results-read request.

Manage the hidden Windows worker from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quarterly_worker.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quarterly_worker.ps1 -Stop
```

The launcher enables bootstrap and records PID/start time. Ignored logs are `backend/.quarterly-worker.stdout.log` and `.stderr.log`. The process stops at machine shutdown; hosting needs a persistent service. Docker Compose supports `docker compose --profile results up -d quarterly-results-worker` after migrations. Set `RESULTS_DATABASE_URL` for external PostgreSQL. A Vercel request alone cannot run this persistent worker.

```dotenv
RESULTS_TICKERS=RELIANCE.NS,TATASTEEL.NS,AAPL,MSFT
RESULTS_BATCH_SIZE=150
RESULTS_REQUEST_DELAY=1
RESULTS_REFRESH_HOURS=24
RESULTS_AI_BATCH_SIZE=8
NEBIUS_API_KEY=
NEBIUS_BASE_URL=https://nebius.ai
NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b
PORT=8000
```

`RESULTS_TICKERS` sets priority only, never a universe cap. Corresponding BSE tickers also get priority. Each batch fairly alternates exchanges, checks up to 150 listings sequentially with one-second pauses, and commits per-listing progress immediately. Successful listings become eligible after 24 hours; unavailable data after seven days; request/storage errors after one hour. Yahoo rate limiting stops the batch and postpones continuation until the next scheduled run. These intervals set eligibility; batch throughput/provider limits determine the full-universe refresh time. It does not download every listing every 15 minutes.

An atomic database-time 14-minute poll lease prevents overlap between workers/manual triggers; a 13-minute job timeout bounds processing. Completed per-listing work survives crashes/timeouts. Admin-only `POST /api/v1/trigger-ingestion` returns 202 and schedules this same bounded worker. Reads do not call Yahoo.

## Financial integrity and NVIDIA/Nebius integration

The Yahoo adapter validates listing identity, exchange, reporting currency, finite numbers and nonfuture report dates. It stores revenue, net income, operating income, diluted/basic EPS, original provider fields and source URL. Operating margin is calculated only with a positive revenue denominator; absent metrics remain null.

Yahoo income-statement calls do not provide reliable announcement dates. `filing_date` stays null and `filing_date_kind` is unavailable. Results sort by **quarter end**. Fiscal labels are inferred from the latest annual period end, with month-end normalization for 52/53-week years, and marked `period_basis: inferred_from_annual_period_end`. Missing/inconsistent fiscal anchors cause rejection instead of guessed periods. The UI explains these date limits.

`stocks` remains the company/listing master. `result_listings` stores catalog membership, ISIN/scrip metadata and durable refresh progress. `quarterly_results` stores raw metrics/JSON, provider provenance, source hashes/revisions and summary work. Its unique key includes `(company_id, provider, fiscal_year, quarter_period)` so FMP and Yahoo are never silently merged. Identical statements preserve summaries; revised/backfilled quarters reset affected summaries. The additive migration retains existing financial data.

After raw data commits, **NVIDIA Nemotron on Nebius Token Factory** selects positive triggers, warning red flags and exactly two executive-summary findings. The server computes YoY/QoQ changes and validates finding IDs before rendering verified sentences. Models cannot invent causes or financial figures. Token Factory's hosted OpenAI-compatible endpoint avoids provisioning a GPU server; this is the integrated Nebius service, without additional Nebius compute/storage services.

The leased summary queue supports retries and rejects stale responses after a revision. Raw financials stay visible while AI is queued/fails. Only a bounded AI batch runs per poll, so initial discovery can create a summary backlog. `--retry-failed` resets failed summaries after fixing configuration/quota. No FMP key is needed for Yahoo; existing credentials are preserved. Nebius credentials remain server-side and paid-provider fallback is not attempted. The nebius.ai website alias resolves to the Token Factory API endpoint.

## API contract

Authenticated `/api` and `/api/v1` aliases:

```text
GET /api/results/latest?market=IN&exchange=NSE&status=all&page=1&page_size=12
GET /api/results?exchange=BSE&q=RELIANCE
GET /api/results/RELIANCE.NS?page_size=100
```

List responses contain one latest Yahoo report per active catalog listing:

```text
items[]:
  company_id, ticker, company_name, exchange, isin, exchange_code
  data_status, checked_at, data_error
  latest_result: null OR financial result with comparisons and AI summary
provider/source: Yahoo Finance/yfinance
total, page, page_size, date_basis
coverage: listed, with_results, pending, ready, unavailable, error
catalog_status: counts and refresh status per exchange
poll_status: last worker run and outcomes
```

`total` includes pending listings. Coverage respects market/exchange/search but excludes the status filter, preserving the denominator. `status=ready` shows successful latest checks. Stored results remain visible if a later check fails. Decimal figures serialize as strings for financial precision. Raw JSON/work tokens are excluded from public responses.

History returns Yahoo quarters ordered newest first. Known listings without reports return an empty history; unknown tickers return 404; bad filters return 422. The old screener snapshot endpoint is `/api/v1/results/imported`; its sixteen-symbol metric-import scope is separate.

## Verification and evidence

[Live API/database evidence](pipeline-live-verification.json) captures actual directory counts, financial records and AI states using isolated in-process authentication; deployed authentication stays enforced. [Browser checks](filings-browser-verification.json) use explicitly synthetic fixtures for loaded/pending/unavailable/retry states, exchange/status/search filters, pagination, history and mobile layout. Historical FMP restrictions are in `fmp-provider-verification.json`.

```powershell
cd backend
$env:DEBUG = 'false'
python -m pytest app/tests/test_filing_pipeline.py app/tests/test_yahoo_results.py app/tests/test_quarterly_results.py -q
python ../docs/quarterly-results/verify_pipeline_live.py
```

Tests cover uncapped catalogs, fiscal boundaries, identity/currency validation, raw persistence, provider isolation, latest-per-listing pagination, summary recovery and fair/rate-limited refresh. Run `npm run build` in `frontend/`. Run `node docs/quarterly-results/verify_filings.cjs` from the root with Vite on port 5186 for browser checks.
