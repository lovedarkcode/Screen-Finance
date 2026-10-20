# Latest quarterly results: reference evidence and implementation

Research and implementation verified on 20 October 2026.

The [exchange-wide Yahoo pipeline](PIPELINE.md) now powers the default `/results`, with full exchange catalogs, paced background discovery, coverage counts and Nemotron summaries. It explicitly labels quarter-end dates and missing announcement dates. The remaining sections describe the earlier screener-snapshot page at `/results/imported`; its curated coverage does not describe the default tracker.

## What Screener.in exposes

The primary reference is the **dedicated results feed**, distinct from user-created stock screens with names such as “All latest quarterly results.”

| Evidence | Observed behavior | Application implication |
| --- | --- | --- |
| [Official industry-filter announcement](https://www.screener.in/docs/changelog/quarterly-results-industry-filter/), updated 10 September 2026 | Describes choosing an industry, comparing Sales, EBIDT, Net profit and EPS, and opening a company's PDF filing. Removing the industry filter preserves the selected date. Industry filtering is a Premium feature. | A results discovery page should combine company figures, industry/date selection and access to original supporting information. |
| [Official product screenshot](https://cdn-media.screener.in/attachments/2026-09-10/1789014780-CleanShot%202026-09-10%20at%2010.02.27%402x.png) linked from that announcement | Screener supplies a screenshot of its industry-filter interface. | This is a reference image supplied by Screener, not a screenshot of a signed-in session captured during this task. |
| [Latest quarterly results](https://www.screener.in/results/latest/) | An unauthenticated request redirects to registration with `next=/results/latest/`. | The live signed-in feed was not inspected. Its exact sorting, growth formulas, ingestion pipeline and update latency have not been established. |
| [Screener's financial-basis explanation](https://support.screener.in/article/41-standalone-or-consolidated) | For screens, consolidated figures are preferred with documented standalone fallbacks; company pages allow switching. | This describes screens/company pages. It does not establish a basis toggle or identical selection logic in the dedicated results feed. |

The reference establishes a user workflow, not access to Screener's implementation or data API. Asset Hunter uses its existing financial provider and does not scrape Screener financial data. YoY/QoQ switching, search, growth sorting and pagination below are application design choices; they were not verified as features of the signed-in Screener feed.

## What was built

Open **Quarterly Results** in the main navigation, or visit `/results/imported` after signing in.

- India, US and all-market selection, industry filtering and company/symbol search.
- Latest available quarter per company or an exact fiscal-period-end selection. Removing an industry preserves the selected reporting quarter. Filter state is shareable in the URL.
- Cards for sales, EBITDA, net profit and EPS, with YoY/QoQ percentage comparisons. EPS prefers diluted figures and explicitly labels a basic-EPS fallback.
- Latest-quarter/name/YoY-sales-growth/YoY-profit-growth sorting and server pagination.
- A comparison dialog with quarterly history, actual comparison dates, explanations for unavailable growth, a company link and the provider statement link.
- Loading, empty, error and retry states; desktop/mobile and light/dark layouts.

`GET /api/v1/results/imported` is authenticated and reads the existing financial tables through the screener's read-only transaction dependency. Accepted parameters are `market=IN|US|ALL`, `quarter=YYYY-MM-DD`, `industry`, `q`, `sort=latest|name|sales_growth|profit_growth`, `page`, and `page_size` (maximum 50). No schema migration, new dependency or LLM call is required.

The importer now retains provider EBITDA and diluted/basic EPS in the quarterly row's existing provenance JSON. Those values pass the same source-record, listing-identity, currency and date validation as the rest of the financial evidence. Existing NLP screening metric semantics remain unchanged. Existing records receive these extra figures on refresh:

```powershell
# From backend, with the Python environment activated
$env:DEBUG = 'false'
python ../scripts/refresh_screener.py
```

Reload results rereads stored data; it does not start a provider import.

## Dates, comparisons and coverage

The existing Yahoo Finance/yfinance feed supplies fiscal period ends rather than reliable announcement timestamps or exchange result PDFs. The UI identifies dates as reporting-period ends, returns `announcement_date: null`, and links to Yahoo financial statements. Standalone/consolidated basis is unspecified by this integration. EBITDA is labeled with the provider's actual field name and is not presented as Screener's EBIDT. An announcement-date feed and original filing links would require an additional exchange/filing data integration.

Missing figures remain unavailable. Financial values need valid provenance, matching row/metric currency and period, and finite numbers. Future reporting dates and unvalidated records are excluded. The listing chooses each company's latest imported validated quarter, not the company most recently refreshed.

YoY uses a comparable quarter 330–400 days earlier; QoQ uses one 75–105 days earlier. The closest eligible date is selected. Growth is `(current / prior - 1) × 100` only when the prior value is positive, currencies agree and source fields agree. This prevents mixing basic and diluted EPS, unrelated quarters or incompatible currencies. Zero/negative prior values produce an unavailable percentage with an explanation. Profit declines from positive profit into loss remain valid negative growth. Fiscal dates are displayed so users can inspect the comparison.

The initial universe has sixteen imported companies, not full exchange coverage. The service groups this curated universe in memory after a parameterized database read; database-side filtering/pagination is the upgrade path for thousands of companies. Latest-source availability and provider limits determine freshness; no continuous announcement ingestion is configured.

## Verification evidence

Final checks passed: 121 backend tests, 14 browser checks, frontend production build and targeted page lint. The build retains the existing large-bundle warning.

- [Backend integrity/API tests](../../backend/app/tests/test_quarterly_results.py): comparable periods, loss baselines, currency/EPS-basis mismatch, missing data, future/annual exclusion, exact-quarter filters, market/search/industry selection, sorting, pagination, authentication, request validation and importer EPS preference.
- [Browser checks](verify.cjs) and [recorded results](browser-verification.json): isolated fixture data and authentication; no real account modifications.
- [Live read-only verification](live-verification.json): configured database responses plus fresh AAPL and TCS.NS provider checks. This file contains public financial evidence, not credentials.

All sixteen starter companies were refreshed successfully during implementation. After refresh, all sixteen had EPS; EBITDA was available for five of eight Indian companies and seven of eight US companies. Provider omissions remain visible as unavailable.

Screenshots using explicit synthetic fixtures: [desktop dark](desktop-dark.png), [desktop light](desktop-light.png), [mobile](mobile.png), and [comparison dialog](comparisons.png).

Screenshots using the saved real database response with isolated browser authentication: [imported data desktop](imported-data-desktop.png) and [imported data mobile](imported-data-mobile.png). These verify rendering of the real financial response, not a live user login.

Reproduce checks from the repository root:

```powershell
node docs/quarterly-results/verify.cjs
```

The browser script expects the local frontend at `http://127.0.0.1:5186` and the existing Playwright installation referenced in the script. Start it with `npm run dev -- --host 127.0.0.1 --port 5186 --strictPort` from `frontend/`.

From `backend/`, with its Python environment activated:

```powershell
$env:DEBUG = 'false'
python -m pytest app/tests/test_quarterly_results.py app/tests/test_financial_evidence.py app/tests/test_nl_screener.py app/tests/test_stock_analysis.py app/tests/test_screener_coverage.py app/tests/test_nebius_client.py -q
python ../docs/quarterly-results/live_check.py --probe-provider
```

The live check only reads the configured database and public financial providers; it does not run imports or call an AI model.
