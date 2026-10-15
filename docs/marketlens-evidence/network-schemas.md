# Observed response schemas

Reference traffic only. No endpoint below is authorized as an Asset Hunter runtime integration. Types describe sampled responses; nullable cases may not all appear. Full response bodies are in [network.json](network.json).

The envelope has `success`, `data`, `error`, `timestamp`, and `meta`. Browser-local induced responses are excluded from these examples.

## `/api/stocks/{ticker}`

Method: `GET`; observed status: `200`.

`data`: object.

| Field | Observed type |
|---|---|
| `id` | `string` |
| `name` | `string` |
| `ticker` | `string` |
| `sector` | `string` |
| `subSector` | `string` |
| `marketCap` | `number` |
| `closePrice` | `number` |
| `lastTradedPrice` | `number` |
| `pchange` | `number` |
| `previousClose` | `number` |
| `openPrice` | `number` |
| `dayHigh` | `number` |
| `dayLow` | `number` |
| `week52High` | `number` |
| `week52Low` | `number` |
| `avgPrice` | `number` |
| `faceValue` | `number` |
| `peRatio` | `number` |
| `industryPe` | `number` |
| `oneDayChange` | `number` |
| `oneWeekReturn` | `number` |
| `oneMonthReturn` | `number` |
| `threeMonthReturn` | `number` |
| `sixMonthReturn` | `number` |
| `oneYearReturn` | `number` |
| `threeYearReturn` | `number` |
| `fiveYearReturn` | `number` |
| `returnOnEquity` | `number` |
| `pbRatio` | `number` |
| `volume` | `number` |
| `avgVolume` | `number` |
| `deliveryQuantity` | `null` |
| `deliveryPercentage` | `number` |
| `beta` | `number` |
| `divYield` | `number` |
| `avgEarnings10Year` | `null` |
| `avgDividendPayout3Year` | `number` |
| `dividendPerShare` | `number` |
| `debtToEquity` | `number` |
| `avgRoce7Year` | `number` |
| `eps` | `number` |
| `bookValue` | `number` |
| `currentRatio` | `number` |
| `netProfit` | `number` |
| `totalDebt` | `number` |
| `totalBorrowings` | `number` |
| `longTermBorrowings` | `number` |
| `shortTermBorrowings` | `number` |
| `revenue` | `number` |
| `opRevenue` | `number` |
| `annVolatility` | `number` |
| `dayVolatility` | `number` |
| `revenueGrowth` | `number` |
| `netMargin` | `number` |
| `ebitdaMargin` | `number` |
| `patGrowth` | `number` |
| `cash` | `number` |
| `interestCover` | `number` |
| `dividendCover` | `number` |
| `assetTurnover` | `number` |
| `dividendPayoutRatio` | `number` |
| `promoterHolding` | `number` |
| `publicHolding` | `number` |
| `shareholders` | `number` |
| `directors` | `null` |
| `priceBandLower` | `number` |
| `priceBandHigher` | `number` |
| `allTimeHigh` | `number` |
| `allTimeLow` | `number` |
| `totalEquity` | `number` |
| `totalAssets` | `number` |
| `currentAssets` | `number` |
| `nonCurrentAssets` | `number` |
| `totalLiabilities` | `number` |
| `currentLiabilities` | `number` |
| `nonCurrentLiabilities` | `number` |
| `totalIncome` | `number` |
| `totalExpense` | `number` |
| `nonCurrentBorrowings` | `number` |
| `currentTax` | `number` |
| `deferredTax` | `number` |
| `totalTaxExpenses` | `number` |
| `operatingCashFlow` | `number` |
| `investingCashFlow` | `number` |
| `netCashFlow` | `number` |
| `dma20` | `number` |
| `dma50` | `number` |
| `dma200` | `number` |
| `lastUpdated` | `string` |
| `description` | `string` |
| `headquarters` | `string` |
| `foundedYear` | `null` |
| `employees` | `null` |
| `ceoName` | `string` |
| `website` | `string` |
| `profitBeforeTax` | `number` |
| `ytdReturn` | `number` |

## `/api/stocks/{ticker}/shareholding`

Method: `GET`; observed status: `200`.

`data`: array (5 sampled items).

| Field | Observed type |
|---|---|
| `quarterEnd` | `string` |
| `promoters` | `number` |
| `publicHolding` | `number` |

## `/api/sector-names`

Method: `GET`; observed status: `200`.

`data`: array (13 sampled items).

Element type: `string`.

## `/api/stocks/{ticker}/quarterly-financials`

Method: `GET`; observed status: `200`.

`data`: array (5 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `totalIncome` | `number` |
| `profitBeforeTax` | `number` |
| `netProfitLoss` | `number` |
| `eps` | `number` |

## `/api/stocks/{ticker}/price-history?period=6M`

Method: `GET`; observed status: `200`.

`data`: array (125 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/peers`

Method: `GET`; observed status: `200`.

`data`: array (7 sampled items).

| Field | Observed type |
|---|---|
| `id` | `string` |
| `name` | `string` |
| `ticker` | `string` |
| `sector` | `string` |
| `subSector` | `string` |
| `marketCap` | `number` |
| `closePrice` | `number` |
| `lastTradedPrice` | `number` |
| `pchange` | `number` |
| `previousClose` | `number` |
| `openPrice` | `number` |
| `dayHigh` | `number` |
| `dayLow` | `number` |
| `week52High` | `number` |
| `week52Low` | `number` |
| `avgPrice` | `number` |
| `faceValue` | `number` |
| `peRatio` | `number` |
| `industryPe` | `null` |
| `oneDayChange` | `number` |
| `oneWeekReturn` | `number` |
| `oneMonthReturn` | `number` |
| `threeMonthReturn` | `number` |
| `sixMonthReturn` | `number` |
| `oneYearReturn` | `number` |
| `threeYearReturn` | `number` |
| `fiveYearReturn` | `number` |
| `returnOnEquity` | `number` |
| `pbRatio` | `number` |
| `volume` | `number` |
| `avgVolume` | `null` |
| `deliveryQuantity` | `null` |
| `deliveryPercentage` | `number` |
| `beta` | `number` |
| `divYield` | `number` |
| `avgEarnings10Year` | `null` |
| `avgDividendPayout3Year` | `null` |
| `dividendPerShare` | `number` |
| `debtToEquity` | `number` |
| `avgRoce7Year` | `number` |
| `eps` | `number` |
| `bookValue` | `number` |
| `currentRatio` | `number` |
| `netProfit` | `number` |
| `totalDebt` | `null` |
| `totalBorrowings` | `number` |
| `longTermBorrowings` | `number` |
| `shortTermBorrowings` | `number` |
| `revenue` | `number` |
| `opRevenue` | `null` |
| `annVolatility` | `null` |
| `dayVolatility` | `null` |
| `revenueGrowth` | `number` |
| `netMargin` | `number` |
| `ebitdaMargin` | `number` |
| `patGrowth` | `number` |
| `cash` | `number` |
| `interestCover` | `number` |
| `dividendCover` | `null` |
| `assetTurnover` | `number` |
| `dividendPayoutRatio` | `null` |
| `promoterHolding` | `number` |
| `publicHolding` | `number` |
| `shareholders` | `null` |
| `directors` | `null` |
| `priceBandLower` | `null` |
| `priceBandHigher` | `null` |
| `allTimeHigh` | `null` |
| `allTimeLow` | `null` |
| `totalEquity` | `number` |
| `totalAssets` | `number` |
| `currentAssets` | `number` |
| `nonCurrentAssets` | `number` |
| `totalLiabilities` | `number` |
| `currentLiabilities` | `number` |
| `nonCurrentLiabilities` | `null` |
| `totalIncome` | `null` |
| `totalExpense` | `null` |
| `nonCurrentBorrowings` | `number` |
| `currentTax` | `null` |
| `deferredTax` | `null` |
| `totalTaxExpenses` | `null` |
| `operatingCashFlow` | `number` |
| `investingCashFlow` | `number` |
| `netCashFlow` | `number` |
| `dma20` | `number` |
| `dma50` | `number` |
| `dma200` | `number` |
| `lastUpdated` | `null` |
| `description` | `null` |
| `headquarters` | `null` |
| `foundedYear` | `null` |
| `employees` | `null` |
| `ceoName` | `null` |
| `website` | `null` |
| `profitBeforeTax` | `null` |
| `ytdReturn` | `null` |

## `/api/search?q={query}`

Method: `GET`; observed status: `200`.

`data`: array (4 sampled items).

| Field | Observed type |
|---|---|
| `id` | `string` |
| `type` | `string` |
| `name` | `string` |
| `ticker` | `string` |
| `description` | `string` |
| `matchScore` | `number` |
| `marketCap` | `number` |

## `/api/stocks/{ticker}/price-history?period=1D`

Method: `GET`; observed status: `200`.

`data`: array (380 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=1W`

Method: `GET`; observed status: `200`.

`data`: array (5 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=1M`

Method: `GET`; observed status: `200`.

`data`: array (20 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=3M`

Method: `GET`; observed status: `200`.

`data`: array (63 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=1Y`

Method: `GET`; observed status: `200`.

`data`: array (246 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=5Y`

Method: `GET`; observed status: `200`.

`data`: array (774 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=10Y`

Method: `GET`; observed status: `200`.

`data`: array (774 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=15Y`

Method: `GET`; observed status: `200`.

`data`: array (774 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=20Y`

Method: `GET`; observed status: `200`.

`data`: array (774 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=25Y`

Method: `GET`; observed status: `200`.

`data`: array (774 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks/{ticker}/price-history?period=30Y`

Method: `GET`; observed status: `200`.

`data`: array (774 sampled items).

| Field | Observed type |
|---|---|
| `date` | `string` |
| `price` | `number` |
| `volume` | `number` |

## `/api/stocks`

Method: `GET`; observed status: `200`.

`data`: object.

| Field | Observed type |
|---|---|
| `filter` | `object` |
| `stocks` | `array` |
| `meta` | `object` |

## `/api/sectors/Banks/stocks`

Method: `GET`; observed status: `200`.

`data`: array (40 sampled items).

| Field | Observed type |
|---|---|
| `id` | `string` |
| `name` | `string` |
| `ticker` | `string` |
| `sector` | `string` |
| `subSector` | `string` |
| `marketCap` | `number` |
| `closePrice` | `number` |
| `lastTradedPrice` | `number` |
| `pchange` | `number` |
| `previousClose` | `number` |
| `openPrice` | `number` |
| `dayHigh` | `number` |
| `dayLow` | `number` |
| `week52High` | `number` |
| `week52Low` | `number` |
| `avgPrice` | `number` |
| `faceValue` | `number` |
| `peRatio` | `number` |
| `industryPe` | `number` |
| `oneDayChange` | `number` |
| `oneWeekReturn` | `number` |
| `oneMonthReturn` | `number` |
| `threeMonthReturn` | `number` |
| `sixMonthReturn` | `number` |
| `oneYearReturn` | `number` |
| `threeYearReturn` | `number` |
| `fiveYearReturn` | `number` |
| `returnOnEquity` | `number` |
| `pbRatio` | `number` |
| `volume` | `number` |
| `avgVolume` | `number` |
| `deliveryQuantity` | `null` |
| `deliveryPercentage` | `number` |
| `beta` | `number` |
| `divYield` | `number` |
| `avgEarnings10Year` | `null` |
| `avgDividendPayout3Year` | `number` |
| `dividendPerShare` | `number` |
| `debtToEquity` | `number` |
| `avgRoce7Year` | `number` |
| `eps` | `number` |
| `bookValue` | `number` |
| `currentRatio` | `number` |
| `netProfit` | `number` |
| `totalDebt` | `number` |
| `totalBorrowings` | `number` |
| `longTermBorrowings` | `number` |
| `shortTermBorrowings` | `number` |
| `revenue` | `number` |
| `opRevenue` | `number` |
| `annVolatility` | `number` |
| `dayVolatility` | `number` |
| `revenueGrowth` | `number` |
| `netMargin` | `number` |
| `ebitdaMargin` | `number` |
| `patGrowth` | `number` |
| `cash` | `number` |
| `interestCover` | `number` |
| `dividendCover` | `number` |
| `assetTurnover` | `number` |
| `dividendPayoutRatio` | `number` |
| `promoterHolding` | `number` |
| `publicHolding` | `number` |
| `shareholders` | `number` |
| `directors` | `null` |
| `priceBandLower` | `number` |
| `priceBandHigher` | `number` |
| `allTimeHigh` | `number` |
| `allTimeLow` | `number` |
| `totalEquity` | `number` |
| `totalAssets` | `number` |
| `currentAssets` | `number` |
| `nonCurrentAssets` | `number` |
| `totalLiabilities` | `number` |
| `currentLiabilities` | `number` |
| `nonCurrentLiabilities` | `number` |
| `totalIncome` | `number` |
| `totalExpense` | `number` |
| `nonCurrentBorrowings` | `number` |
| `currentTax` | `number` |
| `deferredTax` | `number` |
| `totalTaxExpenses` | `number` |
| `operatingCashFlow` | `number` |
| `investingCashFlow` | `number` |
| `netCashFlow` | `number` |
| `dma20` | `number` |
| `dma50` | `number` |
| `dma200` | `number` |
| `lastUpdated` | `string` |
| `description` | `string` |
| `headquarters` | `string` |
| `foundedYear` | `number` |
| `employees` | `null` |
| `ceoName` | `string` |
| `website` | `string` |
| `profitBeforeTax` | `number` |
| `ytdReturn` | `number` |
