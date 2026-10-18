# Stock screener coverage fix — 18 October 2026

## Confirmed findings

The backend resolves `backend/.env` independently of its launch directory and uses PostgreSQL through SQLAlchemy/asyncpg. A read-only query inside the actual FastAPI process confirmed database **screenfinance**, schema **public**, server **::1**, port **5432**. There is no SQLite fallback in the application. SQLite is used only by deterministic tests. No pgAdmin connection profile was supplied; these are the concrete identifiers to compare with that GUI session.

The database contains **16 stocks and 173 financial records**. All 16 stocks have linked financials. Market/exchange counts are **8 Indian/NSE, 5 US/NASDAQ and 3 US/NYSE**. There are currently **no BSE records**. The old `universe_count: 8` counted stocks in the selected market with a validated financial row, not all exchange listings or the number of matching companies.

The assertion that *every* query returns zero was not reproducible against the initial working tree: structured Indian unfiltered and ROE > 0 requests already returned eight companies. An all-market request was rejected with a market clarification. The original five-condition Indian request legitimately has no matches. The following defects were nevertheless confirmed in the query and validation code:

- Even unfiltered searches required an existing validated financial record.
- Default monetary sorting applied a currency WHERE condition that could discard otherwise eligible companies, including those without quote currencies.
- A single latest row per period hid metrics present only in a different report. Exact metric-date selection also depended on a shared row date.
- Market/exchange matching depended on exact stored strings.
- All-market screening was rejected; `without financial filters` hit a blanket exclusion guard.
- Result-cache revision keys used counts and maximum update timestamps, which cannot detect all in-place corrections.
- Empty results did not explain missing values versus unavailable periods versus thresholds that failed.

## Changes

Unfiltered searches retain stock-master rows through outer joins, including companies without financials or market caps. `market: null` means all imported companies. Market capitalization comes directly from `stocks` and does not require a financial snapshot. Monetary sorting groups by currency, retains unknown/null values, and uses symbol/id tie-breakers. Counts are computed before pagination in the same repeatable-read transaction as the page.

Each requested/displayed metric selects its own latest non-null validated value for the requested annual, quarterly, TTM or snapshot basis. Thresholds are applied after that selection, so an older value cannot replace a newer available value merely because the latter fails the threshold. Per-metric provenance retains actual dates, currencies, source and formula. Unknown TTM dates remain unknown. Unverified financial values are not silently treated as reliable data; missing-data explanations and development diagnostics expose that limitation.

Exact `period_end` filters match the metric's provenance date. Optional `as_of` uses stored observation timestamps and excludes later observations/fiscal periods. Current quote values are unavailable historically when their observation is newer or undated. No reporting date or financial value is fabricated.

Exchange aliases such as NSI/XNSE, BOM/XBOM, NMS/NGM/NCM and NYQ are normalized consistently in filtering, serialized results and taxonomy. Financial conditions remain ANDed; unsupported financial OR is rejected explicitly rather than ignored.

Results are read from PostgreSQL on every execution; only parsed requests remain cached. The parser cache version is bumped. Database/connection failures return sanitized HTTP 503 responses. Startup logs include database/schema/host/port without credentials; health errors no longer return raw exception details.

The frontend supports all markets and a distinct screening date, preserves the server's empty-result explanation, and safely renders available monetary values whose currency is unknown.

## Actual financial coverage

These are distinct stocks with a non-null validated value in the named basis, across available stored reports. They are not assertions that every metric has every exact fiscal date.

| Metric | Basis | Stocks with data |
|---|---|---:|
| Market capitalization | Quote snapshot | 16 |
| ROE | Annual / TTM | 16 / 14 |
| P/E | TTM | 15 |
| Revenue growth | Annual | 16 |
| Debt/equity | Snapshot | 16 |
| Net profit margin | Annual / quarterly / TTM | 16 / 16 / 9 |
| Current ratio | Snapshot | 12 |
| Operating margin | Annual | 12 |
| Free cash flow / FCF margin | Annual | 15 / 15 |

Annual report dates span 2022-09-30 through 2026-06-30 across the two markets. Indian annual reports span 2023-03-31 through 2026-03-31. Full period/currency coverage and all 17 metrics are in `coverage-verification.json`.

## SQL and API verification

`verify_coverage.py` compares independent, bound PostgreSQL SQL with SQLAlchemy queries and the real FastAPI ASGI runtime using the configured database. Authentication is overridden only within that isolated verification process; no deployed authentication, accounts or financial records are changed. The running localhost:8000 server was also checked and exposes the updated screener schema.

| Screen | Direct SQL | SQLAlchemy | API |
|---|---:|---:|---:|
| All companies | 16 | 16 | 16 |
| Indian companies | 8 | 8 | 8 |
| US companies | 8 | 8 | 8 |
| Indian NSE or BSE | 8 | 8 | 8 |
| BSE only | 0 | 0 | 0 |
| Indian annual ROE > 0 | 8 | 8 | 8 |
| US annual ROE > 0 | 6 | 6 | 6 |
| Original five financial conditions | 0 | 0 | 0 |
| Annual growth > 5 and P/E < 25 | 3 | 3 | 3 |

The linked-financials query independently returned 16 in both raw SQL and SQLAlchemy. The three matches in the final example are ICICIBANK.NS, RELIANCE.NS and SBIN.NS; that example does not replace or relax the original request. For the original request, the sequential Indian candidate counts are 8 market, 8 exchanges, 5 ROE, 3 debt/equity, then 0 annual growth. The exclusion at that stage is a failed condition, not missing data.

Live NVIDIA interpretation was also executed for all companies without filters, all Indian companies, Indian ROE > 0, and the original NSE/BSE five-condition request. All returned HTTP 200 with the expected preserved filters and counts **16, 8, 8, 0**. The first sandboxed provider attempt failed; the authorized network-enabled verification succeeded. No thresholds or production records were altered to obtain matches.

## Verification and reproduction

- **139 backend tests passed**, plus three subtests, including stock/AI/financial evidence, authentication, screening, connection errors, count/pagination, missing data, historical periods and updates without timestamp changes.
- **44 browser checks passed**, including all markets, null currency, screening-date payloads, empty explanations, existing stock-analysis navigation, mobile/desktop layout and no runtime errors.
- Changed frontend component passes ESLint. Production build passes; the pre-existing large-bundle warning remains.
- Browser fixtures still emit existing HomePage list-key and chart-sizing console warnings; there were no uncaught page exceptions.
- Two old auth tests were repaired to use isolated in-memory users and a test-only signing key, rather than expecting hardcoded live credentials and a two-character registration password to work. Authentication application behavior was not changed.

With the existing backend environment activated, from the repository root:

```powershell
$env:DEBUG = 'false'
python -m pytest backend/app/tests -q
python scripts/diagnose_screener.py
python scripts/diagnose_screener.py --market IN
python scripts/diagnose_screener.py --screen-file docs/nl-screener/exchange-screen.json
python docs/nl-screener/verify_coverage.py --ai
```

Diagnostics refuse non-development environments before querying. They report actual connection identity, counts, period/currency/metric coverage, and candidate counts before/after each filter with disjoint exclusion reasons. No diagnostic HTTP endpoint or SQL is exposed to ordinary users.

The local venv launcher points to an older Python installation, so verification used installed Python 3.14 with the existing venv's site-packages on PYTHONPATH, without installing dependencies. Pytest plugin autoload was disabled because an unrelated system `platformdirs.pytest_plugin` entry point is missing; the project's pytest-asyncio plugin was loaded explicitly.

## Exact files changed in this fix

Application code:

- `backend/app/services/screener/query_builder.py`
- `backend/app/services/screener/validator.py`
- `backend/app/services/screener/parser.py`
- `backend/app/services/screener/metrics.py`
- `backend/app/agents/screener/graph.py`
- `backend/app/schemas/screener.py`
- `backend/app/api/v1/screener.py`
- `backend/app/main.py`
- `frontend/src/components/screener/NaturalLanguageScreener.jsx`

Tests, diagnostics and documentation:

- `backend/app/tests/test_nl_screener.py`
- `backend/app/tests/test_screener_coverage.py` (new)
- `backend/app/tests/test_auth.py`
- `scripts/diagnose_screener.py`
- `docs/nl-screener/verify_coverage.py` (new)
- `docs/nl-screener/verify.cjs`
- `docs/nl-screener/README.md`
- `docs/nl-screener/COVERAGE_FIX.md` (this report)
- `docs/nl-screener/coverage-verification.json` (new SQL/API evidence)
- `docs/nl-screener/coverage-ui/verification.json`, `empty-390.png`, `empty-1440.png`, `feed-dark-1440.png`, `feed-dark-390.png`, `feed-light-1440.png`, `feed-light-390.png` (new isolated browser evidence)

## Remaining limits

Coverage is the existing 16-company imported universe, not every exchange listing. No BSE companies are currently imported, although BSE and its aliases are tested. Financial OR, FX conversion, multi-year/CAGR screens and unsupported ratios still return explicit unsupported/clarification responses. Historical screening is conservative about stored observation dates; overwritten snapshots and historical listing membership cannot be reconstructed from the current schema. Unknown fiscal ends cannot match exact dates. These limits are reported rather than filled with invented data. No migrations, dependency additions, production refreshes, financial writes or deployments were performed.
