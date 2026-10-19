# Market news

The home feed loads six live market headlines from `/api/v1/news`.
The backend combines Indian and US market RSS feeds, removes duplicates,
sorts by publication time, and returns article links. The interface displays
headlines and publication times without a feed-provider label. Article content
opens on the original destination in a new tab.

The active page refreshes every five minutes. Redis shares the five-minute
cache across function instances. If both feeds fail, previously fetched data
can be shown for up to one hour with a visible notice; older data is not served.
The fallback cache is bounded to 64 keys within each process when Redis is
unavailable. Partial feed availability is indicated. News failures do not
refresh or disrupt the rest of the market page.

`/api/v1/news?symbol=AAPL` supports individual symbols, and limits are validated
from 1 through 50. The existing `/news/trending` endpoint returns latest market
headlines; the provider supplies no popularity score.

Verification: 153 backend tests and three subtests passed; frontend build and
lint passed. `node docs/market-news/verify.cjs` tests loading, links, dates,
provider-label removal, mobile layout, retry, stale/empty states and retention
of headlines during refresh failures. Its screenshots use isolated fixtures.
