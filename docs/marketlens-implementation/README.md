# Asset Hunter stock detail implementation

Implemented on 15 October 2026 following the owner's instruction to proceed with the redesign and leave Claude out of scope.

The existing `/stock/:symbol` route, Axios client, authentication and Redux state remain in use. The stock route now has a dedicated Asset Hunter header and continuous full-width section layout. Other application routes retain their existing layout. No packages were installed. Poppins font assets were obtained from the official Google Fonts repository; their license is included in `frontend/public/fonts/OFL.txt`.

## Finished page

| View | Dark | Light |
|---|---|---|
| TCS, 1440px desktop | [Screenshot](asset-hunter-TCS-desktop-dark.png) | [Screenshot](asset-hunter-TCS-desktop-light.png) |
| TCS, 390px mobile | [Screenshot](asset-hunter-TCS-mobile-dark.png) | [Screenshot](asset-hunter-TCS-mobile-light.png) |
| AEROFLEX, same ticker as reference | [Desktop](asset-hunter-AEROFLEX-desktop-dark.png) | [Mobile](asset-hunter-AEROFLEX-mobile-dark.png) |

## Side-by-side visual review

Reference screenshots are observation evidence only and are not shipped in the frontend bundle. Both columns use the same viewport width. Asset Hunter captures use live data from its own Yahoo/yfinance-backed endpoints. A synthetic identity was supplied only inside the isolated Playwright browser to exercise protected screens; application authentication was not modified.

- [Desktop comparison with all section crops](comparison-desktop.html) · [full-page PNG](comparison-desktop.png)
- [Mobile comparison with all section crops](comparison-mobile.html) · [full-page PNG](comparison-mobile.png)

| Section | Desktop comparison | Mobile comparison | Remaining difference |
|---|---|---|---|
| Header | [PNG](comparison-desktop-header.png) | [PNG](comparison-mobile-header.png) | Asset Hunter name and existing artwork replace all reference branding; no beta lockup. |
| Company/price summary | [PNG](comparison-desktop-summary.png) | [PNG](comparison-mobile-summary.png) | Price, classification, quote timestamp and link destination use the configured provider. |
| Area chart | [PNG](comparison-desktop-chart.png) | [PNG](comparison-mobile-chart.png) | Actual price series, history bounds and currency ticks differ with provider data; controls support all 12 reference periods. |
| Key metrics | [PNG](comparison-desktop-metrics.png) | [PNG](comparison-mobile-metrics.png) | Provider P/E/EPS and adjusted historical extrema differ. Face value remains unavailable where not supplied. Metric selection works. |
| Price range | [PNG](comparison-desktop-range.png) | [PNG](comparison-mobile-range.png) | VWAP is shown as unavailable rather than an invented daily average. Other fields use actual provider values. |
| Returns | [PNG](comparison-desktop-returns.png) | [PNG](comparison-mobile-returns.png) | Returns are computed from adjusted provider history. AEROFLEX lacks the five-year lookback, so it shows a dash. |
| Ownership/financial band | [PNG](comparison-desktop-panels.png) | [PNG](comparison-mobile-panels.png) | Provider ownership is a current insider/institution/other-holder snapshot, without fabricated reporting dates. Available financial data reports total revenue, labeled accurately. The collapsed statement extension adds a small row below the charts. |
| Company profile | [PNG](comparison-desktop-about.png) | [PNG](comparison-mobile-about.png) | Provider description, headquarters, incorporation year and executive availability differ. |
| Peers | [PNG](comparison-desktop-peers.png) | [PNG](comparison-mobile-peers.png) | Peer universe comes from existing Asset Hunter sector lists, with real quote/valuation enrichment. Mobile shows symbols and retains inner table scrolling. |

The visual pass corrected the initial font fallback, excess card line heights, mobile price wrapping, chart height, legend spacing and mobile table column widths. Data-dependent values, missing fields and the intentional extensions remain different from the reference. Perfect pixel identity is not claimed.

## Interactions and checks

- Production frontend build passed. Vite retains its existing large-bundle warning.
- Targeted lint passed for the redesigned components, page and route layout. Repository-wide lint still reports existing errors in older components, pages and configuration; it was not treated as passing.
- **11 backend tests passed**, including previous-session quote changes, real market timestamps, intraday history without volume, unavailable long-term returns, finite ratios, lakh/EPS conversion, ownership availability and 404 distinction.
- **All 12 timeframe requests returned HTTP 200** during live browser verification: [results](range-checks.json).
- **15 interaction checks passed**, covering search navigation, sector navigation, peer links, preference persistence, metric editing, Escape dismissal, empty states, quote retry, repeated range selection and failed-statement loading: [results](interaction-checks.json).
- No uncaught browser errors were observed. Full-page captures at 390px had no document-level horizontal overflow; the peer table scrolls within its own container.
- Loading, empty and provider-failure screenshots below use browser-local request interception. They demonstrate UI behavior, not actual provider outages.

| State | Screenshot |
|---|---|
| Loading skeleton | [PNG](state-loading.png) |
| Missing stock | [PNG](state-not-found.png) |
| Retryable provider failure | [PNG](state-provider-error.png) |
| Empty ownership and financial data | [PNG](state-empty-panels.png) |
| Search results | [PNG](state-search-results.png) |
| EPS chart | [PNG](07-eps-desktop.png) |
| Expanded company description | [PNG](08-company-expanded.png) |
| Expanded financial statements | [PNG](10-statements-desktop.png) |

## Backend changes

- Added `/api/v1/stocks/{symbol}/overview` for numeric fundamentals, price ranges, adjusted-history returns, profile data and computed highlights.
- Added `/api/v1/stocks/{symbol}/shareholding` for the provider's available current ownership snapshot.
- Extended the existing chart endpoint with intraday and all reference timeframes while retaining old range aliases and legacy fields.
- Extended the existing quarterly statement response with numeric chart data. Amounts convert to lakhs; EPS remains rupees per share.
- Enriched the existing peer endpoint with price, daily change, market cap and P/E.
- Corrected quote timestamps and previous-session change, debt/equity units, unavailable data and provider-404 handling.

No runtime frontend/backend requests to Market Lens APIs were introduced. Existing unrelated provider stubs were left unchanged. Claude and the existing AI stubs were not connected or invoked.
