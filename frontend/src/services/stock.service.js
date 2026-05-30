export const mockStock = {
  symbol: 'AAPL',
  name: 'Apple Inc.',
  price: 195.27,
  change: 1.72,
  changePercent: 0.89,
  date: '23 May 2026, 04:00 PM EDT',
  marketStatus: 'Market Closed',
  exchange: 'NASDAQ',
  country: 'US',
}

export const mockMetrics = [
  { label: 'Market Cap', value: '$2,996,858 Cr.' },
  { label: 'Current Price', value: '$195.27' },
  { label: 'High / Low', value: '$198.62 / $164.08' },
  { label: 'Stock P/E', value: '31.26' },
  { label: 'Book Value', value: '$4.70' },
  { label: 'Dividend Yield', value: '0.48 %' },
  { label: 'ROCE', value: '38.72 %' },
  { label: 'ROE', value: '147.11 %' },
  { label: 'Face Value', value: '$0.10' },
  { label: 'Promoter holding', value: '0.06 %' },
  { label: 'ROCE 5Yr', value: '35.18 %' },
  { label: 'Sales', value: '$3,94,328 Cr.' },
  { label: 'PEG Ratio', value: '2.44' },
  { label: 'Debt', value: '$1,18,950 Cr.' },
  { label: 'EPS', value: '$6.24' },
  { label: 'Industry PE', value: '28.11' },
  { label: 'OPM', value: '30.58 %' },
  { label: 'ROE 10Yr', value: '92.39 %' },
  { label: 'Price to book value', value: '41.55' },
  { label: 'Debt to equity', value: '1.22' },
  { label: 'ROE 5Yr', value: '106.29 %' },
]

const months = ['Jun 2025', 'Aug 2025', 'Oct 2025', 'Dec 2025', 'Feb 2026', 'Apr 2026']
const seedPrices = [165, 172, 180, 188, 184, 195]
export const mockChartData = months.map((m, i) => ({
  month: m,
  price: seedPrices[i],
  volume: 80_000_000 + Math.round(Math.sin(i) * 40_000_000 + 60_000_000),
}))

const quarterCols = [
  'Mar 2024', 'Jun 2024', 'Sep 2024', 'Dec 2024', 'Mar 2025',
  'Jun 2025', 'Sep 2025', 'Dec 2025', 'Mar 2026',
]

export const mockQuarters = {
  columns: quarterCols,
  rows: [
    { label: 'Sales',            values: ['90,753','85,777','94,930','124,300','90,753','85,777','94,930','124,300','95,359'] },
    { label: 'Expenses',         values: ['53,902','49,635','54,447','68,855','53,912','49,649','54,856','69,052','53,667'] },
    { label: 'Operating Profit', values: ['36,851','36,142','40,483','55,445','36,841','35,928','40,074','55,049','41,692'] },
    { label: 'OPM %',            values: ['40.61%','42.12%','42.61%','44.62%','40.58%','41.90%','42.19%','44.28%','43.72%'] },
    { label: 'Net Profit',       values: ['23,636','21,448','24,196','36,330','23,686','21,448','23,482','35,248','24,780'] },
    { label: 'EPS ($)',          values: ['1.53','1.40','1.54','2.36','1.53','1.40','1.52','2.30','1.62'] },
  ],
}

export const mockSummaryTables = {
  profitLoss: {
    title: 'Profit & Loss',
    columns: ['Mar 2026', 'Mar 2025'],
    rows: [
      { label: 'Sales',            values: ['$3,94,328', '$3,83,285'] },
      { label: 'Expenses',         values: ['$2,12,981', '$2,08,285'] },
      { label: 'Operating Profit', values: ['$1,81,347', '$1,75,000'] },
    ],
  },
  balanceSheet: {
    title: 'Balance Sheet',
    columns: ['Mar 2026', 'Mar 2025'],
    rows: [
      { label: 'Equity Capital', values: ['$67,045',   '$62,697'] },
      { label: 'Reserves',       values: ['$1,34,402', '$1,21,513'] },
      { label: 'Borrowings',     values: ['$1,18,950', '$1,08,345'] },
    ],
  },
  cashFlow: {
    title: 'Cash Flow',
    columns: ['Mar 2026', 'Mar 2025'],
    rows: [
      { label: 'Operating Cash Flow', values: ['$67,045', '$1,10,543'] },
      { label: 'Investing Cash Flow', values: ['-$89,520','-$94,321'] },
      { label: 'Financing Cash Flow', values: ['-$30,437','-$23,167'] },
    ],
  },
  ratios: {
    title: 'Ratios',
    columns: ['Mar 2026', 'Mar 2025'],
    rows: [
      { label: 'ROCE', values: ['38.72%', '37.12%'] },
      { label: 'ROE',  values: ['147.11%','143.21%'] },
      { label: 'ROIC', values: ['32.43%', '30.21%'] },
    ],
  },
}

export const mockAISummary = {
  summary:
    'Apple Inc. is a global technology leader specializing in iPhone, Mac, iPad, Wearables and Services. Strong brand, high customer loyalty and consistent financial performance drive long-term value.',
  keyPoints: [
    'Strong ecosystem and brand loyalty',
    'Services segment growing rapidly',
    'Robust cash flows and profitability',
    'Exposure to China remains a key risk',
    'Innovation in AI and wearables to watch',
  ],
}

export const mockAbout = {
  description:
    'Apple Inc. designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories worldwide.',
  founded: '1976',
  headquarters: 'Cupertino, California, USA',
  website: 'www.apple.com',
}

export const mockRelated = [
  { name: 'Microsoft Corp.',     symbol: 'MSFT',  price: 415.75,   changePercent: 1.21 },
  { name: 'NVIDIA Corporation',  symbol: 'NVDA',  price: 1037.89,  changePercent: 1.32 },
  { name: 'Alphabet Inc.',       symbol: 'GOOGL', price: 167.34,   changePercent: 0.85 },
  { name: 'Meta Platforms, Inc.',symbol: 'META',  price: 475.92,   changePercent: -0.35 },
  { name: 'Amazon.com, Inc.',    symbol: 'AMZN',  price: 182.63,   changePercent: 0.73 },
]

const stockService = {
  getStock: () => Promise.resolve(mockStock),
  getMetrics: () => Promise.resolve(mockMetrics),
  getChart: () => Promise.resolve(mockChartData),
  getQuarters: () => Promise.resolve(mockQuarters),
}

export default stockService
