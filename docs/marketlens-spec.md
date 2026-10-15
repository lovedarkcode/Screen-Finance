# Asset Hunter stock detail — Market Lens observation spec

**Status: redesign implemented following approval on 15 October 2026. Claude integration is deferred at the owner's request.** See the [implementation review and screenshots](marketlens-implementation/README.md).

Observed on 15 October 2026 (IST) at [AEROFLEX](https://marketlens.nseindia.com/stocks/AEROFLEX); also tested [RELIANCE](https://marketlens.nseindia.com/stocks/RELIANCE) through search. This document specifies layout and behavior for **Asset Hunter**. Reference prices are capture examples, not Asset Hunter data or verified market facts.

## 1. Branding and scope

- The website name must be **Asset Hunter**, exactly as clarified by the owner. The current `Assest Hunter` spelling in the navigation needs correction during Phase 2.
- Use the existing Asset Hunter artwork. Do not reproduce the reference logo, acronym wordmark, Market Lens product lockup, beta branding, favicon, or proprietary images.
- Reference screenshots necessarily show the reference's branding; they are observation evidence only and must not ship as application assets.
- Recreate the page structure, spacing, themes, charts, controls, and responsive behavior using Asset Hunter components and data.
- Header and page copy must identify Asset Hunter. Reference actions bearing exchange branding should become neutral actions such as `View exchange quote` and `Advanced chart`. Exchange names may still describe a stock's actual listing venue; they are not the site's identity.
- Asset Hunter must never call the observed reference APIs from either frontend or backend. Their URLs below document observation only.
- Preserve the existing `/stock/:symbol` route, protected-route behavior, Redux authentication, Axios client, stock service, and unrelated screens. The existing Screener destination is `/screens`.
- Install no dependencies without asking first. Phase 1 used an existing Python Playwright installation and existing Chromium binaries.

## 2. Evidence and method

A visible Chromium browser rendered the live SPA through Playwright. Navigations waited for network idle; XHR/fetch responses were recorded from browser traffic. Desktop was configured at **1440 × 1000**, mobile at **390 × 844**, device scale approximately 1. Full-page screenshots cover the entire document. Separate captures show controls and alternate states.

Main captures:

| Capture | Evidence |
|---|---|
| Desktop, dark | [Full page](marketlens-evidence/desktop-1440-dark-full.png) |
| Desktop, light | [Full page](marketlens-evidence/desktop-1440-light-full.png) |
| Mobile, dark | [Full page](marketlens-evidence/mobile-390-dark-full.png) |
| Mobile, light | [Full page](marketlens-evidence/mobile-390-light-full.png) |
| All states | [Evidence index](marketlens-evidence/README.md) |
| Recorded response bodies | [XHR/fetch log](marketlens-evidence/network.json) |
| Response field types | [Network schemas](marketlens-evidence/network-schemas.md) |
| Computed styles | [Dark](marketlens-evidence/tokens-dark.json), [light](marketlens-evidence/tokens-light.json), [mobile](marketlens-evidence/tokens-mobile-dark.json) |

**Evidence labels:** normal captures show live, unmodified responses. Files beginning `induced-` show browser-local request interception to expose loading, empty, or HTTP 500 behavior. These are controlled experiments, not claims that the live service failed. No interception code is part of the application.

## 3. Page inventory, top to bottom

The reference is one continuous scrolling page. It has no page-wide Overview/Analysis/Statements tab bar and no permanent sidebar. The eight managed sections are chart, metrics, range, returns, shareholding, financial result, about, and peers. The stock identity/price summary remains above them.

| Order | Region | Desktop composition | Required data |
|---|---|---|---|
| 0 | Fixed header | Brand left; search; manage sections and theme right; compact quote appears after scrolling | Site identity; symbol, price, absolute and percentage change; search results; preferences |
| 1 | Stock summary | Company name and industry pill; ticker and broader classification; large price/change; quote link; timestamp | `name`, `ticker`, `sector`, `subSector`, price, previous close, change, change %, currency, market timestamp, quote URL |
| 2 | Price Chart | Heading/link left, segmented ranges right; full-width area chart | Ordered timestamp/price points; selected range; currency |
| 3 | Key Metrics | Heading left; metric search/edit toolbar right; five-column card grid | Metric IDs, labels, numeric values, units, availability; selected custom metric IDs |
| 4 | Price Range | Two horizontal range cards; four supporting cards below | Day low/high, 52-week low/high, current price, open, previous close, volume, VWAP, timestamp |
| 5 | Returns Performance | Seven equal return cards in one row | Returns for 1W, 1M, 3M, 6M, 1Y, 3Y, 5Y; availability |
| 6 | Shareholding Pattern | Left card of a two-column band; dated tabs, legend, donut, two summary values | Reporting dates; promoter/public percentages; optional additional holder categories when actually available |
| 7 | Financial Result | Right card of same band; Results/EPS tabs, legend, grouped bars | Quarterly dates, total income, pretax profit, net profit/loss, EPS, units |
| 8 | About company | Collapsible description followed by four compact fact cards | Description, headquarters, incorporation year, CEO, website |
| 9 | Peer Comparison | Rounded table with six example rows and five columns | Company name/ticker, price, day change %, market cap, P/E, navigation symbol |

### 3.1 Header, stock summary, and search

- Fixed translucent header with blur, bottom border, and matching centered content width. The stock summary scrolls away; a compact ticker/price/change replaces its space in the desktop header while scrolling. Mobile prioritizes the brand and icon buttons.
- Search opens a centered overlay, rather than exposing a permanent header text input. It contains a multiline-capable text field, close button, submit/search icon, rotating suggestion text, and sector chips. The reference offers 13 sector chips from a separate request.
- Typing a ticker displays matching stock suggestions. Enter with `RELIANCE` navigated to its stock page. Sector browsing and peer-row navigation were tested separately; destinations are recorded in the evidence.
- Unmatched search shows an empty-result message and a hint to try a company, ticker, or sector. Escape dismisses search. Capture the open, typed, suggestion, no-result, and sector states.
- Selecting an Asset Hunter result must navigate using its existing provider symbol, e.g. `/stock/RELIANCE.NS`, rather than copying the reference's bare-ticker routing.
- The summary displays last traded price prominently, a direction icon and signed change, classification, and an IST timestamp. Do not use the browser's current time as if it were the quote's market timestamp.
- The reference has external quote/chart links and a company website link opening a new tab. Keep functional destinations only; neutral labels must not imply Asset Hunter is the exchange.

### 3.2 Price chart

- Default **6M**. Main controls: **1D, 1W, 1M, 3M, 6M, 1Y, 5Y**. Chevron menu: **10Y, 15Y, 20Y, 25Y, 30Y**. All 12 selections were exercised and captured.
- Selected segment has a lavender fill in dark mode and deep purple in light mode; inactive segments have muted text. The dropdown overlays the chart and closes after selecting a range.
- A thin smooth price line has a fading area fill. Currency ticks are on the left, dates underneath. The normal chart has no volume bars, volume toggle, or persistent price legend. Intraday uses time labels; long histories use month/year labels.
- Hover shows a vertical cursor, an active point, and a small date/price tooltip. Do not render the chart as a decorative static image.
- Range changes request a different history period. Keep previous data or a stable-sized skeleton during fetch, then replace it; prevent an earlier request from overwriting a later selection.
- Empty history shows `No price data available`. Do not turn absence into a zero-price line. Keep history bounds limited to actual listing/provider coverage, even if the user selects a longer range.
- Reference `date` values are ISO calendar dates for daily history and millisecond epoch **strings** for intraday. Normalize these into an explicit timestamp in Asset Hunter.

### 3.3 Key metrics

- Default seven cards, ordered: **Market Cap, P/E Ratio, EPS, Face Value, All Time High, All Time Low, Debt/Equity**. Desktop wraps after five; mobile after two.
- Labels are small/muted; values are semibold. Market cap uses Indian crore units and INR prices use the rupee symbol. Missing values show a dash.
- Search is an anchored field beside Edit Metrics. In this browser session, queries including EPS and ROE produced an empty ratio dropdown while the default seven cards stayed visible. No new metric-search network request occurred.
- Edit Metrics changes its label/style to Done. Clicking it and hovering a card exposed **no working add/remove controls** in the inspected session. Do not claim the reference supports tested metric reordering, dragging, or a metric-edit modal.
- Reference local storage contains an empty custom-ratio preference list. **Proposed Asset Hunter completion:** retain the same toolbar appearance, but make customization useful with a small selector using metrics already supplied by Asset Hunter; keyboard-selectable results, selected indicators, remove controls while editing, and locally persisted IDs. Keep the default seven fixed unless changed by the user. This completion is a deliberate proposal for approval, not an observed reference capability.
- Historical all-time extremes require historical coverage. A 52-week extreme must not be relabeled as an all-time value. Provider-unavailable face value or extrema remain unavailable.

### 3.4 Price range and returns

- Range cards show low in loss color and high in gain color, joined by a track with one lavender position marker. They are **read-only indicators**, not draggable sliders.
- Position uses `(price − low) / (high − low)`, clamped to 0–100%. Missing/invalid bounds and equal low/high need a defined unavailable state, without division errors.
- Supporting cards are Open, Prev Close, Volume, VWAP. Volume uses Indian lakh/crore notation. Compute VWAP only from appropriate trade/intraday data; do not relabel an unweighted daily average as VWAP.
- Returns are read-only cards with timeframe, direction icon, signed percentage, and gain/loss color. The reference's seven displayed periods start at one week; the section-manager description mentioning 1D is not an extra visible card.
- A displayed reference five-year zero does not establish that Asset Hunter should substitute zero for unavailable history. Use null/unavailable when the provider lacks the lookback. Use consistent adjusted-price history and disclose the relevant as-of date.

### 3.5 Shareholding

- Latest reporting date is selected initially. A horizontally scrollable segmented strip contains up to five returned reporting dates. All five AEROFLEX dates were selected and captured.
- Changing dates updates the donut and percentages locally, with no additional endpoint request. The older September/December report changed the displayed split from 65.47/34.53 to 66.99/33.01 in this capture.
- Actual observed API data contains **promoters and public holding only**. Although the manager description mentions institutional holders, do not assume FII/DII series exist.
- Teal promoter segment, orange public segment; central hole; corresponding dots/labels above; two values separated from the chart by a horizontal rule below. Hover captures cover both segments. The reference tooltip displays a percentage in a white box even in dark mode; Asset Hunter can keep the percentage while using readable theme-appropriate tooltip colors and an accessible category label.
- **Reference defect:** empty or HTTP 500 shareholding responses still produced unrelated fallback percentages (54.16/15.07). Asset Hunter must display a clear unavailable state instead. Never invent quarters or historical ownership splits from a current snapshot.

### 3.6 Quarterly financial result

- Two tabs: **Results** (default) and **Earnings Per Share**. They reuse the already loaded quarterly records.
- Results groups three bars per quarter: teal total income, amber profit before tax, blue net profit/loss. Latest report is on the left. Display five available periods, without manufacturing missing quarters.
- EPS switches to a single EPS series and appropriate rupee units. Maintain the card dimensions between tabs.
- Hover over a quarter shows its reporting date and series values. The Results tooltip displays three amounts in lakhs; the EPS tooltip shows EPS. Legend items in the observed DOM are labels, not independent toggle buttons.
- Heading states amounts in **₹ Lakhs**. Asset Hunter currently returns statement cells formatted in crore strings; obtain raw numeric values before charting and convert deliberately (`INR / 100000`). EPS is a per-share rupee figure and must not receive the lakh conversion.
- Empty/failed financial data showed `No financial data available` while retaining the heading and tabs.

### 3.7 Company profile and peers

- Description initially has a roughly three-line desktop clamp; mobile shows a compact multi-line preview. `Read more` expands it and changes to `Show less`; expanding changes document height without navigation or another API call.
- Four fact cards: headquarters, incorporation year, MD/CEO, website. Missing incorporation year displayed a dash for AEROFLEX; RELIANCE had a year.
- Treat provider descriptions as text or sanitized content; do not inject third-party HTML unchecked. Company website destinations must use valid HTTP(S) URLs.
- Peer table columns: **Company, Price, 1D Change, Market Cap, P/E Ratio**. Company cell has a primary name and a smaller ticker underneath. Numeric columns align right; change is a tinted rounded badge with arrow. Rows highlight on hover and navigate on click. No sort buttons, peer filter, or pagination were visible on this detail page.
- On mobile the table retains its columns within an overflow container; swipe/scroll to see the right-hand columns. The page itself should not acquire horizontal overflow.
- Empty peer data removed the entire peer section in the reference. Proposed Asset Hunter behavior keeps a useful `No peers available` state when that section is enabled, so users can distinguish missing data from a hidden preference.
- The reference's headline P/E differed from its peer-row P/E for the same company. Asset Hunter should use a consistent calculation basis and date instead of reproducing this discrepancy.

## 4. Manage sections and persistent preferences

- Right-side, full-height drawer over a dimmed and blurred page; its header and footer remain anchored around a scrollable list. Desktop drawer is approximately 340px wide in the captured viewport; mobile occupies most of the screen.
- Eight rows pair an icon, title, brief description, and switch. Every switch was toggled off and restored. Hiding a section removes it from the document flow. Shareholding and financial result can be hidden independently; the remaining panel should use available width.
- Footer has Reset to Default and Done; header has close X. Reset restores all eight sections. Visibility persistence through reload was tested. Theme preference also persisted through subsequent page loads.
- Use Asset Hunter-specific local-storage keys and versionable metric IDs. Do not copy reference-branded keys into the application.
- Provide semantic switches with checked state, descriptive labels, keyboard operation, focus trapping and return, and reduced-motion support. Reference visual parity does not require copying its missing accessibility labels.

## 5. States and error behavior

| State | Reference evidence/behavior | Asset Hunter target |
|---|---|---|
| Initial load | Request held in browser; complete page skeleton, header blocks, quote placeholders, large chart rectangle, lower card placeholders | Same visual skeleton structure with stable dimensions, `aria-busy`, no fake quote |
| Range fetch | Different period requested; chart transitions | Stable chart frame, loading indication, last-selection-wins behavior |
| Search empty | Unmatched query returns empty array and a help message | Same layout with Asset Hunter copy and existing search service |
| Metric search empty | No matching ratios; default cards remain | Useful selector with clear empty results, subject to approval above |
| Individual missing field | Dash, e.g. missing incorporation year | Dash for null; preserve actual numeric zero |
| Chart empty/500 | Empty-history message | Empty vs retryable fetch error distinguished |
| Financial empty/500 | Financial-data message; tabs retained | Same stable frame; accurate empty/error text |
| Shareholding empty/500 | Fallback percentages remained | No fabricated data; explicit unavailable message |
| Peers empty/500 | Section disappears | Enabled section shows no-peer/error state |
| Unknown symbol | HTTP 404, centered `Stock not found`, ticker-specific explanation, `Go to Screener` button | Same flow; button goes to existing `/screens` |
| Quote server failure | Simulated HTTP 500 also becomes Stock not found | Separate retryable provider/network failure; reserve not-found for a confirmed missing stock |

Unknown-symbol navigation was tested using `ZZZNOSTOCK123`; the reference button navigated to `/screener`. Simulated failures were browser-local and removed after capture. Asset Hunter must preserve optional-section isolation: a financial or AI error must not erase a successfully loaded stock quote.

## 6. Observed network contracts — observation only

All paths in this table belong to `https://marketlens.nseindia.com`; **none is an application integration target**. Ordinary requests below use GET, with no request body.

Common JSON envelope:

```text
{ success: boolean, data: object | array | null, error: string | null,
  timestamp: ISO string, meta: null | {page, limit, total, hasMore} }
```

| Observed path | Response shape | When used |
|---|---|---|
| `/api/stocks/{ticker}` | Envelope with stock/profile/metrics object | Stock navigation/reload |
| `/api/stocks/{ticker}/price-history?period=6M` | `data: [{date: string, price: number, volume: number}]` | Initial chart and range selection; `period` takes all 12 values above |
| `/api/stocks/{ticker}/shareholding` | `data: [{quarterEnd: string, promoters: number, publicHolding: number}]` | Stock navigation; date tabs consume this array locally |
| `/api/stocks/{ticker}/quarterly-financials` | `data: [{date: string, totalIncome: number, profitBeforeTax: number, netProfitLoss: number, eps: number}]` | Stock navigation; Results/EPS local |
| `/api/stocks/{ticker}/peers` | `data: Stock[]`; many stock fields unused by the table | Stock navigation |
| `/api/sector-names` | `data: string[]` | Initial load/search sector chips |
| `/api/search?q=RELIANCE` | `data: [{id, type, name, ticker, description, matchScore, marketCap}]` | Search text changes; no result is `data: []` |

Stock object fields used by the layout:

```text
identity: id, name, ticker, sector, subSector
quote: lastTradedPrice, closePrice, previousClose, pchange, lastUpdated
range: openPrice, dayHigh, dayLow, week52High, week52Low, avgPrice, volume
metrics: marketCap, peRatio, eps, faceValue, allTimeHigh, allTimeLow, debtToEquity
returns: oneWeekReturn, oneMonthReturn, threeMonthReturn, sixMonthReturn,
         oneYearReturn, threeYearReturn, fiveYearReturn
profile: description, headquarters, foundedYear, ceoName, website
```

The recorded stock object has additional valuation, profitability, balance-sheet, cash-flow, and moving-average fields. The linked network schema appendix inventories their observed types. Only request/compute data needed by the enabled components.

Observed irregularities to normalize: nullable fields; zeros with unclear availability; intraday timestamps encoded as strings; some negative intraday volume values; financial units differing from the current backend; a timezone-less `lastUpdated`. Do not import these data-quality quirks into Asset Hunter.

**Refresh cadence:** requests were triggered by navigation, reload, range selection, and search input. Shareholding/financial tabs and section preferences did not request new data. A **55.02-second idle observation produced zero XHR/fetch requests**, after Indian cash-market hours; see `refresh-observation.json`. This cannot establish trading-hours behavior, an undocumented server cache TTL, or a universal refresh interval. Do not invent one. Initial Asset Hunter behavior should preserve load-on-navigation and range-driven fetches; any live refresh should use the user's provider limits and return its actual as-of time.

## 7. Computed design tokens and responsive rules

Values below come from computed styles, not color guesses from the supplied images. Reference body font is **Poppins, system-ui, -apple-system, sans-serif**. At both inspected widths the computed root/body size was **15px** and body line height **22.5px**. Use a legitimate font source; do not copy reference font binaries. No font package has been installed.

| Token | Dark | Light |
|---|---|---|
| Page / surface 0 | `#101019` | `#ffffff` |
| Card / surface 1 | `#181822` | `#ffffff` |
| Surface 2 | `#1c1c28` | `#ffffff` |
| Alternate band / surface 3 | `#24242d` | `#f1f3f9` |
| Primary text | `#e5e5e8` | `#202224` |
| Secondary text | `#ccccd1` | `#606060` |
| Muted text | `#ababb2` | `#717d8a` |
| Accent | `#b7b4e7` | `#3a2e7d` |
| Accent surface | `#1c1640` | `#3a2e7d14` |
| Accent border | `#635ec8` | `#3a2e7d33` |
| Gain | `#66d696` | `#00b69b` |
| Loss | `#f5a9a9` | `#f93c65` |
| Subtle border | `#24242d` | `#32416814` |
| Default border | `#42424b` | `#32416826` |
| Strong border | `#62626b` | `#32416840` |
| Small shadow | `0 1px 3px #0006` | `0 1px 3px #0000000a` |
| Medium shadow | `0 4px 14px #00000059` | `6px 6px 54px #0000000d` |
| Large shadow | `0 8px 30px #00000080` | `0 8px 30px #00000014` |

Chart series: teal `#00b69b`, public orange `#e65c1b`, pretax amber `#f5a623`, net-profit blue approximately `#3b82f6`. The line follows the active accent. The header's dark glass background is `#101019d9` with a 24px blur.

| Dimension / typography | Observed value or rule |
|---|---|
| Content container | `80rem` maximum, approximately **1200px** at the measured root; centered, `1rem` side padding |
| Fixed header | `3.5rem`, approximately **52.5px**; matching top offset on main |
| Stock summary padding | `1.75rem` top and bottom, approximately **26.25px** |
| Main section padding | `2rem` top and bottom, approximately **30px** |
| Common gaps | `.5rem`, `.75rem`, `1rem`, `1.5rem`, `2rem` ≈ **7.5, 11.25, 15, 22.5, 30px** |
| Card padding | `1rem` metric/range cards; `1.25rem` chart panels ≈ **15 / 18.75px** |
| Company title | **22.5px / 33.75px**, weight **600** |
| Section heading | **18.75px / 28.125px**, weight **600**; small accent bar before it |
| Metric/value text | approximately **13.125px**; value weight **600**, label **11.25px** |
| Main price | **28.125px / 33.75px**, weight **700** |
| Compact controls | range text **11.25px**, metric edit/manage buttons inline **12px** |
| Table headers | **10px**; padding approximately **9.375px 15px** |
| Table cells | padding approximately **11.25px 15px** |
| Radius scale | observed rounded controls around **9–12px**, cards around **15–18px**, pill controls fully rounded; use linked computed records for each component |
| Price chart frame | approximately **270px high** at desktop; responsive width |
| Ownership chart | approximately **180 × 180px** wrapper; outer/inner pie radii **80/50** chart units |
| Financial chart | approximately **281px high** in captured desktop panel |
| Motion | common transitions **150–300ms**, small hover-scale effects; chart animations must finish before comparison screenshots |

Responsive utility boundaries present in the reference are `sm`/`md`/`lg` at the usual 40/48/64rem media conditions (nominal **640/768/1024px**); final implementation must verify the boundary states as well as the two captured widths.

| Region | Small/mobile | Intermediate | Wide desktop |
|---|---|---|---|
| Header search | Icon opens same search overlay | Full search trigger from md | Compact scroll quote plus full trigger |
| Summary | Company pill and price/change wrap | Fluid | Mostly single-line identity/price row |
| Chart toolbar | Heading above wrapping controls | Fluid | Controls right of heading |
| Metrics | 2 columns | 3 from sm | 5 from lg |
| Range cards | 1 column | 2 from md | 2 |
| Open/close/volume/VWAP | 2 columns | 4 from sm | 4 |
| Returns | 3 columns | 5 from sm | 7 from lg |
| Ownership/financials | Stacked | Stacked | 2 columns from lg |
| Profile facts | 2 columns | Expands | 4 compact cards |
| Peer table | Horizontal inner scroll | Horizontal if needed | All columns visible |

The 390px capture includes long headings wrapping, ownership dates scrolling within their strip, a final lone five-year-return card, and financial tabs fitting inside the stacked panel. Preserve these behaviors without shrinking the entire desktop page.

## 8. Map to this codebase after approval

| Existing asset | Reuse / required extension |
|---|---|
| `frontend/src/Routes.jsx` | Keep `/stock/:symbol`; not-found CTA uses `/screens` |
| `frontend/src/components/common/Navbar.jsx` | Retain authentication and app navigation; apply Asset Hunter spelling/identity; stock-specific header composition must not break other pages |
| `frontend/src/layouts/Mainlayouts.jsx` | Current global padded container prevents full-bleed bands; add only a stock-route layout accommodation |
| `frontend/src/pages/Stock/StockPage.jsx` | Retain data-loading/state patterns; replace the detail composition and currently cosmetic tab strip |
| `frontend/src/components/stock/StockHeader.jsx` | Rework into reference-like company/price summary; preserve working watchlist access elsewhere in the app |
| `frontend/src/components/stock/StockChart.jsx` | Reuse installed Recharts and stock service; area chart, left currency axis, ranges and tooltips |
| `frontend/src/services/api.js` | Keep base URL, auth interceptors and timeout behavior |
| `frontend/src/services/stock.service.js` | Keep existing quote/search/chart/metrics/financial/profile/peer calls; add minimal section methods only where needed |
| `backend/app/api/v1/stocks.py` | Existing live integration uses Yahoo chart/search and yfinance; extend these authorized sources, without reference API calls |
| Existing quarterly/annual statements | Reuse raw provider data and current statement routes; add pretax profit and EPS numerics for the quarterly chart |
| `/stocks/{symbol}/peers` | Current response has search metadata, not all required comparison figures; enrich with the user's quote/metric sources |
| Shareholding | No historical shareholding endpoint found; add only data actually supported by the user's providers; show unavailable when absent |
| `/stocks/{symbol}/summary` and AI services | Current stock summary is templated; AI summary/orchestration files are stubs. Wire real computed metrics and the owner's Claude configuration before labeling content AI-generated |

Keep existing successful response contracts backward compatible. Prefer additive raw numeric fields or a small section endpoint over rewriting all current routes into the reference envelope. Frontend adapters can map existing `price/changePercent` to the view model, `month` to a proper chart timestamp, and formatted statements to dedicated numeric chart data supplied by the backend. Preserve currency and units explicitly; do not parse currency-formatted strings to do calculations.

Existing packages already provide React, Redux, Axios, Recharts, Tailwind, Lucide icons, dialogs, animation, FastAPI, httpx, pandas and yfinance. A new chart library or state-management system is unnecessary.

### Project-specific additions proposed for approval

The live reference has no AI insights panel and no balance-sheet/cash-flow tab group on this stock page. To preserve Asset Hunter capabilities while matching the observed core sequence:

1. Keep the nine content regions above in the same order (summary plus eight managed sections).
2. Provide **Financial statements** as a collapsed extension below the financial charts, reusing the existing quarterly, profit/loss, balance-sheet, cash-flow and ratios components/routes.
3. Add an optional **Asset Hunter Insights** section after peers, controlled from Manage sections. Use computed metrics for factual highlights. When the owner's Claude layer is available, show a grounded summary with data timestamps and sources; otherwise show an accurate unavailable state or clearly identified computed highlights. No fabricated recommendations or placeholder company summaries.
4. Implement useful metric selection and accurate empty/retry states as explicitly identified above.

These additions, corrected error behavior, and neutral link labels are intentional departures from the reference. They are subject to approval with this spec.

## 9. Phase 2 delivery and verification

Build only after approval, in small section commits: (1) Asset Hunter shell/search/theme and tokens, (2) summary, (3) chart, (4) metrics, (5) ranges/returns, (6) ownership, (7) financials, (8) company/peers, (9) project extensions and state polish. Include each section's required backend fields with that section rather than making an unrelated backend rewrite.

For each section, capture Asset Hunter and the relevant reference at identical **1440px** and **390px** viewports and theme; produce side-by-side artifacts and a concrete visual-difference list. Fix spacing, typography, colors, grid behavior, clipping, and control states before continuing. Real data values and Asset Hunter branding are expected to differ. Existing reference captures are local comparison evidence and must not be bundled into the frontend.

Verify actual interactions, keyboard/focus behavior, range fetch races, missing data, 404 vs provider failures, preference persistence, and units. Run the existing frontend build/lint and relevant backend checks appropriate to the changes. Reuse the current working environment; ask before installing anything.

**Implementation update:** the owner approved proceeding with the redesign and explicitly deferred Claude. The core sections, financial statement extension, computed highlights, accurate unavailable states, and Asset Hunter branding are implemented. The observation notes above preserve the reference behavior; the implementation review records intentional data and branding differences.
