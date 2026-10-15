# Asset Hunter: shared Feed, Screens and stock UI

Implemented 15 October 2026. No dependencies installed. Existing routes, Redux authentication, Axios client, stock service and watchlist service are retained. No NSE branding or private API integration was added.

## What changed

- Feed, Screens and stock detail share the same Asset Hunter header, stock/sector search, account/saved-list links, persistent theme, Poppins typography and stock design tokens.
- Mobile navigation wraps into a second header row. Feed and Screens have active route indicators; stock detail retains its Manage Sections drawer and compact scrolling quote.
- Feed uses the stock page's actual chart component for selectable benchmarks and all existing chart ranges. Index cards, sector discovery, movers, breadth and news use the same cards, section bands and lavender accents as stock detail.
- Screens uses sector pills, a sector summary, a searchable/sortable constituent table, quote refresh, stock-detail links and watchlist controls. The selected sector is reflected in the URL and browser history. Narrow tables scroll inside their own container.
- Loading, empty, unavailable-quote and retry states use the same visual language. Slow responses from a previous sector cannot replace the selected sector. A watchlist outage does not prevent sector or quote loading.

## Data behavior

Feed previously displayed invented fallback prices, random four-second price fluctuations, artificial sparklines, fixed sentiment claims and hard-coded news headlines. Those have been removed. Prices and chart history now come from the existing backend stock endpoints; missing quotes remain unavailable. Market refresh requests current provider data without inventing live ticks. The eight-company sample is explicitly labeled; movers and breadth are computed only from available sample data. The old “active” list sorted by share price; its replacement is an honestly labeled alphabetical “All tracked” list, alongside gainers and losers.

The existing `/news` endpoint currently returns no articles, so Feed displays its news empty state. Claude and AI generation remain deferred as requested. Backend API code was not changed for this task.

## Visual review

Full-page screenshots use actual 1440px desktop and 390px mobile viewports. Each page has dark and light captures. Quote data comes from the running local backend. Authentication and initial empty watchlist responses were supplied only inside an isolated browser context for review; production authentication was not changed.

| Page | Desktop dark | Desktop light | Mobile dark | Mobile light |
| --- | --- | --- | --- | --- |
| Feed | [Screenshot](feed-dark-1440.png) | [Screenshot](feed-light-1440.png) | [Screenshot](feed-dark-390.png) | [Screenshot](feed-light-390.png) |
| Screens | [Screenshot](screens-dark-1440.png) | [Screenshot](screens-light-1440.png) | [Screenshot](screens-dark-390.png) | [Screenshot](screens-light-390.png) |

Matching-viewport side-by-side comparisons use the redesigned Asset Hunter stock page as the style reference. Desktop images are scaled equally within the comparison artifact; source viewport widths remain 1440px.

- [Feed / stock desktop](feed-vs-stock-1440.png), [Screens / stock desktop](screens-vs-stock-1440.png)
- [Feed / stock mobile](feed-vs-stock-390.png), [Screens / stock mobile](screens-vs-stock-390.png)
- [Feed before](feed-before-1440.png), [Screens before](screens-before-1440.png)
- [Mobile movers detail](feed-mobile-movers.png), [Screener error state](screens-error-390.png)

Review fixes: index-card change colors now retain the shared gain/loss colors; the breadth card no longer stretches to the full mover-table height; all Feed mover columns fit at 390px; Screens explains horizontal table scrolling. Theme screenshots disable transitions to avoid capturing intermediate colors.

Remaining visual differences are content-specific: Feed has benchmark cards and discovery panels, Screens has sector controls and a constituent table, and stock detail has company-specific sections. They use identical fonts, container widths, header, tokens, button treatments and section-heading patterns. Screens retains horizontal scrolling for its five-column data table on mobile. No known unintended page overflow remains at tested widths.

## Verification

- Production build passed. Existing >500 kB bundle warning remains.
- ESLint passed for all six changed JSX files.
- [35 browser checks](verification.json) passed, with zero runtime errors. Covers sector deep links, filter/reset, numeric sort and null placement, average calculation, pending watchlist controls, add/remove, quote refresh, theme continuity, benchmark/chart selection, mover filtering, news empty/error states, search-to-stock routing, account links, error retries, independent watchlist failure and stale-response protection.
- Feed, Screens and stock detail were checked for page overflow at 1440, 1024, 768 and 390px.

Run the saved browser check against the running frontend:

```powershell
node docs/shared-ui/verify.cjs
```

The check uses deterministic API fixtures in its isolated browser context, including synthetic authentication. It does not change backend or user data. It uses the already-installed Python Playwright driver; set `PLAYWRIGHT_PATH` to another existing Playwright package path if needed.

Local implementation commits:

- `64bc4cb`: shared navigation and theme.
- `3059d40`: Screens redesign.
- `56d8a4c`: Feed redesign and shared benchmark chart.

Pre-existing modified backend Python cache files were left untouched and excluded from commits.
