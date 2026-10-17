# Indian and US stock analysis

Implemented 17 October 2026 using the existing Yahoo Finance/yfinance provider. No additional dependency, API key, stock-master import, or database migration is required. Listings are searched and loaded on demand.

Search by company name or ticker, for example Apple, `AAPL`, Microsoft, `MSFT`, Ford, `F`, or `BRK-B`. NSE/BSE symbols such as `TCS.NS` and `TCS.BO` continue to work. US share-class input such as `BRK.B` is normalized to Yahoo's `BRK-B`; preferred symbols such as `BAC-PL` are accepted too. Search results identify the exchange and currency.

The search endpoint now includes equities from supported Indian and US exchange codes and excludes other countries, funds and crypto results. US direct links use the existing `/stock/AAPL` route. Quotes, overview metrics, return history, charts, ownership, financial statements and sector peer comparisons use the same analysis page. US peer candidates come from a curated US sector sample, matching the existing Indian-sector approach. Available data varies by ticker and provider; missing values retain the existing unavailable states.

Prices and market capitalization use the listing currency. Statements, revenue and quarterly charts use the provider's financial reporting currency, which may differ for an ADR. There is no FX conversion or relabeling of USD amounts as INR. Indian statements retain crore units and quarterly chart amounts retain lakhs; other reporting currencies use millions. EPS is not divided by the monetary scale. Price charts and quote timestamps use the exchange timezone, including US daylight saving time. Mixed-market watchlists format each quote independently.

The Feed benchmark/sample lists and sector Screener remain Indian-market discovery views. US companies are available through the shared search and direct stock links; `scripts/sync_us_stocks.py` remains an unused stub because this route does not depend on a stock-master database.

## Verification

- 21 backend regression tests cover Indian compatibility, US listing metadata, single-letter and share-class symbols, preferred shares, bounded search limits, statement units, EPS scaling, ADR reporting currency, same-market peers, symbol encoding and 404 handling.
- [21 US browser checks](verification.json) cover search-to-analysis routing, dollar prices and metrics, New York intraday labels, USD financials/statements, mixed watchlists, ADR currencies and both themes at desktop/mobile widths.
- [35 shared UI checks](shared-regression.json) and [43 ChaiUI checks](chaiui-regression.json) pass against the updated frontend.
- [6 live browser checks](live-browser-verification.json) loaded real Apple quotes, charts, fundamentals and statements, then searched for and opened Microsoft. Only `/auth/me` was supplied as a fixture in that isolated browser; market-data requests reached the running local backend.
- A separate live-provider smoke check passed for AAPL, MSFT, BRK-B, F and TCS.NS quotes; Apple/Microsoft/F/TCS searches; and Apple's overview, quarterly results and ownership.
- Production build, changed-file ESLint and `git diff --check` pass. The existing large-bundle build warning remains.

Run backend checks from `backend` with the existing environment:

```powershell
$env:DEBUG = 'false'
.\venv\Scripts\python.exe -m pytest app/tests/test_stocks.py app/tests/test_stock_detail.py app/tests/test_us_stocks.py
```

`DEBUG=false` is set only for the test process; the workstation's inherited `DEBUG=release` prevents settings from parsing. No `.env` file was edited.

With Vite running, use its actual port:

```powershell
$env:APP_URL = 'http://127.0.0.1:5174'
node docs/us-market/verify.cjs
node docs/us-market/live_browser.cjs
```

The live browser check also requires the local backend. Both scripts use an isolated browser and do not write backend/user data. The first uses synthetic market fixtures; screenshots below are from that fixture check and are not real quotes. `PLAYWRIGHT_PATH` can point to another installed Playwright driver.

For an optional direct provider check from `backend`:

```powershell
.\venv\Scripts\python.exe ..\docs\us-market\live_check.py
```

| Theme | Desktop | Mobile |
| --- | --- | --- |
| Dark | [Apple analysis](apple-dark-1440.png) | [Apple analysis](apple-dark-390.png) |
| Light | [Apple analysis](apple-light-1440.png) | [Apple analysis](apple-light-390.png) |

Provider reference: [yfinance financial data](https://ranaroussi.github.io/yfinance/reference/yfinance.financials.html), [provider exchange codes](https://github.com/ranaroussi/yfinance/blob/main/yfinance/const.py).
