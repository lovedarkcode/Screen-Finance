# ChaiUI migration

Implemented 17 October 2026 using the official [ChaiCode ChaiUI registry](https://ui.chaicode.com/r/registry.json). Components are owned locally under `frontend/src/components/ui`, as intended by ChaiUI's copy-in workflow. Source URLs are recorded in each imported component. The registry's TypeScript was converted to JSX and its internal imports updated to this project's aliases.

Feed, Screens, stock detail, authentication and watchlist now use ChaiUI buttons, icon buttons, search inputs, form fields, cards, tables, segmented controls, dialogs, status chips, skeletons, spinners and toast notifications. Existing reusable stock table/action components also use the shared primitives. ChaiUI's tab, textarea and dropdown primitives replace the previous versions at their existing paths. Google continues to render its own configured sign-in button.

The theme uses ChaiUI's Manrope typography, warm borders, asymmetric buttons and light/dark tokens. Existing page grids and responsive rules remain in the page stylesheets. The saved theme also drives the document root so portalled dropdowns and notifications match the page. Watchlist uses the same header and theme as Feed, Screens and stock detail.

ChaiUI's registry has no chart component. Price, financial and ownership charts continue to render with the existing Recharts dependency and API data. Their controls, cards, tooltips and colors now follow the shared theme. Financial values, rupee formatting, available timeframes, filtering, sorting, watchlist requests and authentication endpoints are preserved.

Local adaptations: Card supports `asChild` for native buttons, links and articles; Dialog accepts page theme attributes and initial focus, uses React's effect event for current close behavior, and handles focus trapping without focus resets while typing; ToastProvider clears its timers on unmount. Authentication fields keep react-hook-form refs and connect errors through `aria-describedby` and `aria-invalid`.

`frontend/components.json` now includes `@chaiui`. To add another component from the frontend directory:

```powershell
npx shadcn add @chaiui/component-name
```

Review overwrites of existing components because the local adaptations above must be retained. The unused legacy Sheet and Sonner files remain; the routed application uses ChaiUI Dialog and ToastProvider.

## Verification

Run Vite on port 5173, then from the repository root:

```powershell
$env:UI_VERIFY_OUTPUT_DIR = "$PWD/docs/chaiui"
node docs/shared-ui/verify.cjs
node docs/chaiui/verify.cjs
```

These use isolated API and authentication fixtures and do not modify the backend or user data. `PLAYWRIGHT_PATH` can point to another installed Playwright driver. Screenshots use synthetic fixture quotes, not market prices.

- [Existing UI regression results](verification.json): 35 checks.
- [ChaiUI behavior results](chaiui-verification.json): chart ranges and retry, EPS/ownership/statement controls, metric persistence, company description, search focus and keyboard trapping, search outage, watchlist success/failure/retry, dismissible notifications, login and registration payloads, validation accessibility, and layout in both themes at 1440 and 390 pixels.
- Production build and ESLint on changed JavaScript/JSX files pass. The full-repository lint command still reports pre-existing issues in untouched placeholder files and `vite.config.js`. The existing bundle-size warning remains.

| View | Desktop dark | Mobile light |
| --- | --- | --- |
| Feed | [Preview](feed-dark-1440.png) | [Preview](feed-light-390.png) |
| Screens | [Preview](screens-dark-1440.png) | [Preview](screens-light-390.png) |
| Stock detail | [Preview](stock-dark-1440.png) | [Preview](stock-light-390.png) |
| Watchlist | [Preview](watchlist-dark-1440.png) | [Preview](watchlist-light-390.png) |
| Search dialog | [Preview](search-dark-1440.png) | [Preview](search-light-390.png) |

[Mobile authentication validation](login-390.png). Matching light/dark desktop/mobile captures for each view are also stored alongside this file.
