import { ExternalLink } from 'lucide-react'
import { PriceChange } from './StockUI'
import { marketTime, money } from './stock-format'

export default function StockHeader({ stock, profile = {} }) {
  const industry = profile.industry || stock.industry
  const sector = profile.sector || stock.sector
  return <section className="stock-section stock-summary"><div className="stock-container">
    <div className="stock-identity"><h1>{stock.name}</h1>{industry && industry !== 'N/A' && <span className="stock-industry">{industry}</span>}</div>
    <div className="stock-classification"><span>{stock.baseSymbol || stock.symbol}</span><span>{stock.exchange} · {stock.currency || 'INR'}</span>{sector && sector !== 'N/A' && <span>{sector}</span>}</div>
    <div className="stock-price-row"><strong className="stock-price">{money(stock.price, stock.currency)}</strong><PriceChange value={stock.changePercent} absolute={stock.change} />
      <a href={`https://finance.yahoo.com/quote/${encodeURIComponent(stock.symbol)}/`} target="_blank" rel="noreferrer"><ExternalLink size={14} />View market quote</a>
    </div><p className="stock-timestamp">as on {marketTime(stock.date, stock.timeZone)}</p>
  </div></section>
}
