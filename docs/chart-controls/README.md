# Shared chart controls

Stock detail and home benchmark charts share timeframes, Price/P/E selection,
linear/log scales, and independently switchable Price, 50 DMA, 100 DMA and Volume.
Daily averages use supplemental daily closes with a lookback before the visible
range. Intraday averages use completed prior sessions. Missing data stays missing.

P/E displays positive trailing valuation snapshots from the database at their
observation timestamps. The existing ingestion updates snapshots; it does not
provide a complete historical daily P/E feed. No historical values are invented.

Alerts are saved per symbol in this browser and poll once per minute while that
chart is mounted. They trigger once, can be replaced or removed, and do not send
email or monitor after the page closes. Provider quotes may be delayed.

Verification: backend indicator/stock-detail/US-stock tests, frontend build and
ESLint, and `node docs/chart-controls/verify.cjs` against Vite on port 5178.
Browser checks use mocked data; screenshots are fixtures, not live market claims.
