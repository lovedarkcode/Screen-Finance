# Market Lens reference evidence

Captured 15 October 2026 for the Asset Hunter stock-detail specification. Reference branding in these browser screenshots is evidence only; it must not be copied into the shipped application.

Browser: visible Chromium via existing Playwright. Desktop viewport 1440 × 1000; mobile viewport 390 × 844. Full-page captures extend vertically. Other screenshots show the current viewport, often scrolled to the relevant section.

Normal captures use live responses. `induced-` captures use browser-local interception to hold a request, return an empty array, or return HTTP 500. They do not establish a live service outage.

## Main full-page captures

- [Desktop dark](desktop-1440-dark-full.png)
- [Desktop light](desktop-1440-light-full.png)
- [Mobile dark](mobile-390-dark-full.png)
- [Mobile light](mobile-390-light-full.png)

## Records

- [Specification](../marketlens-spec.md)
- [XHR/fetch response log](network.json)
- [API-only HAR, cookies/auth headers removed](reference-xhr.har)
- [Additional computed layout details](layout-details.json)
- [Response field schemas](network-schemas.md)
- [Refresh observation](refresh-observation.json)
- [Dark computed styles](tokens-dark.json)
- [Light computed styles](tokens-light.json)
- [Mobile computed styles](tokens-mobile-dark.json)

## All captured states

Each screenshot has an accompanying JSON record with its URL and page text (most also include the viewport). Chart, tooltip, modal, search, section-toggle, mobile, and error states are listed below.

| State | Screenshot | State record |
|---|---|---|
| about expanded | [PNG](about-expanded.png) | [JSON](about-expanded.json) |
| back to screener | [PNG](back-to-screener.png) | [JSON](back-to-screener.json) |
| chart more ranges | [PNG](chart-more-ranges.png) | [JSON](chart-more-ranges.json) |
| chart price tooltip | [PNG](chart-price-tooltip.png) | [JSON](chart-price-tooltip.json) |
| chart range 10y | [PNG](chart-range-10y.png) | [JSON](chart-range-10y.json) |
| chart range 15y | [PNG](chart-range-15y.png) | [JSON](chart-range-15y.json) |
| chart range 1d | [PNG](chart-range-1d.png) | [JSON](chart-range-1d.json) |
| chart range 1m | [PNG](chart-range-1m.png) | [JSON](chart-range-1m.json) |
| chart range 1w | [PNG](chart-range-1w.png) | [JSON](chart-range-1w.json) |
| chart range 1y | [PNG](chart-range-1y.png) | [JSON](chart-range-1y.json) |
| chart range 20y | [PNG](chart-range-20y.png) | [JSON](chart-range-20y.json) |
| chart range 25y | [PNG](chart-range-25y.png) | [JSON](chart-range-25y.json) |
| chart range 30y | [PNG](chart-range-30y.png) | [JSON](chart-range-30y.json) |
| chart range 3m | [PNG](chart-range-3m.png) | [JSON](chart-range-3m.json) |
| chart range 5y | [PNG](chart-range-5y.png) | [JSON](chart-range-5y.json) |
| chart range 6m | [PNG](chart-range-6m.png) | [JSON](chart-range-6m.json) |
| desktop 1440 dark full | [PNG](desktop-1440-dark-full.png) | [JSON](desktop-1440-dark-full.json) |
| desktop 1440 light full | [PNG](desktop-1440-light-full.png) | [JSON](desktop-1440-light-full.json) |
| desktop edit metrics | [PNG](desktop-edit-metrics.png) | [JSON](desktop-edit-metrics.json) |
| desktop manage sections | [PNG](desktop-manage-sections.png) | [JSON](desktop-manage-sections.json) |
| financial eps tooltip | [PNG](financial-eps-tooltip.png) | [JSON](financial-eps-tooltip.json) |
| financial eps | [PNG](financial-eps.png) | [JSON](financial-eps.json) |
| financial results tooltip | [PNG](financial-results-tooltip.png) | [JSON](financial-results-tooltip.json) |
| global search no results | [PNG](global-search-no-results.png) | [JSON](global-search-no-results.json) |
| global search open | [PNG](global-search-open.png) | [JSON](global-search-open.json) |
| global search results | [PNG](global-search-results.png) | [JSON](global-search-results.json) |
| global search sector | [PNG](global-search-sector.png) | [JSON](global-search-sector.json) |
| global search suggestions | [PNG](global-search-suggestions.png) | [JSON](global-search-suggestions.json) |
| global search typed | [PNG](global-search-typed.png) | [JSON](global-search-typed.json) |
| induced empty sections | [PNG](induced-empty-sections.png) | [JSON](induced-empty-sections.json) |
| induced initial loading | [PNG](induced-initial-loading.png) | [JSON](induced-initial-loading.json) |
| induced main api error | [PNG](induced-main-api-error.png) | [JSON](induced-main-api-error.json) |
| induced section errors | [PNG](induced-section-errors.png) | [JSON](induced-section-errors.json) |
| manage preferences persisted | [PNG](manage-preferences-persisted.png) | [JSON](manage-preferences-persisted.json) |
| manage price chart hidden | [PNG](manage-price-chart-hidden.png) | [JSON](manage-price-chart-hidden.json) |
| manage reset | [PNG](manage-reset.png) | [JSON](manage-reset.json) |
| manage toggle 1 | [PNG](manage-toggle-1.png) | [JSON](manage-toggle-1.json) |
| manage toggle 2 | [PNG](manage-toggle-2.png) | [JSON](manage-toggle-2.json) |
| manage toggle 3 | [PNG](manage-toggle-3.png) | [JSON](manage-toggle-3.json) |
| manage toggle 4 | [PNG](manage-toggle-4.png) | [JSON](manage-toggle-4.json) |
| manage toggle 5 | [PNG](manage-toggle-5.png) | [JSON](manage-toggle-5.json) |
| manage toggle 6 | [PNG](manage-toggle-6.png) | [JSON](manage-toggle-6.json) |
| manage toggle 7 | [PNG](manage-toggle-7.png) | [JSON](manage-toggle-7.json) |
| manage toggle 8 | [PNG](manage-toggle-8.png) | [JSON](manage-toggle-8.json) |
| metrics edit hover | [PNG](metrics-edit-hover.png) | [JSON](metrics-edit-hover.json) |
| metrics search empty | [PNG](metrics-search-empty.png) | [JSON](metrics-search-empty.json) |
| metrics search eps | [PNG](metrics-search-eps.png) | [JSON](metrics-search-eps.json) |
| metrics search roe | [PNG](metrics-search-roe.png) | [JSON](metrics-search-roe.json) |
| mobile 390 dark full | [PNG](mobile-390-dark-full.png) | [JSON](mobile-390-dark-full.json) |
| mobile 390 light full | [PNG](mobile-390-light-full.png) | [JSON](mobile-390-light-full.json) |
| mobile about expanded | [PNG](mobile-about-expanded.png) | [JSON](mobile-about-expanded.json) |
| mobile chart dropdown | [PNG](mobile-chart-dropdown.png) | [JSON](mobile-chart-dropdown.json) |
| mobile edit metrics | [PNG](mobile-edit-metrics.png) | [JSON](mobile-edit-metrics.json) |
| mobile financial eps | [PNG](mobile-financial-eps.png) | [JSON](mobile-financial-eps.json) |
| mobile manage sections | [PNG](mobile-manage-sections.png) | [JSON](mobile-manage-sections.json) |
| mobile peer table | [PNG](mobile-peer-table.png) | [JSON](mobile-peer-table.json) |
| mobile search | [PNG](mobile-search.png) | [JSON](mobile-search.json) |
| mobile shareholding tab | [PNG](mobile-shareholding-tab.png) | [JSON](mobile-shareholding-tab.json) |
| peer hover | [PNG](peer-hover.png) | [JSON](peer-hover.json) |
| peer navigation | [PNG](peer-navigation.png) | [JSON](peer-navigation.json) |
| shareholding 03 feb 2026 | [PNG](shareholding-03-feb-2026.png) | [JSON](shareholding-03-feb-2026.json) |
| shareholding 30 jun 2026 | [PNG](shareholding-30-jun-2026.png) | [JSON](shareholding-30-jun-2026.json) |
| shareholding 30 sep 2025 | [PNG](shareholding-30-sep-2025.png) | [JSON](shareholding-30-sep-2025.json) |
| shareholding 31 dec 2025 | [PNG](shareholding-31-dec-2025.png) | [JSON](shareholding-31-dec-2025.json) |
| shareholding 31 mar 2026 | [PNG](shareholding-31-mar-2026.png) | [JSON](shareholding-31-mar-2026.json) |
| shareholding tooltip 1 | [PNG](shareholding-tooltip-1.png) | [JSON](shareholding-tooltip-1.json) |
| shareholding tooltip 2 | [PNG](shareholding-tooltip-2.png) | [JSON](shareholding-tooltip-2.json) |
| stock not found | [PNG](stock-not-found.png) | [JSON](stock-not-found.json) |
| global search escape closed | [PNG](global-search-escape-closed.png) | [JSON](global-search-escape-closed.json) |
