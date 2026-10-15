import { Link } from 'react-router-dom'
import { EmptyState, PriceChange, SectionTitle } from './StockUI'
import { money, number } from './stock-format'

export default function StockPeers({ peers = [], loading, error }) {
  return <section className="stock-section stock-band" id="peers"><div className="stock-container"><SectionTitle>Peer Comparison</SectionTitle>
    {loading ? <div className="sk sk-panel" /> : error ? <EmptyState error>Peer comparison is temporarily unavailable.</EmptyState> : !peers.length ? <EmptyState>No peers available</EmptyState> : <div className="stock-peer-scroll" tabIndex={0} role="region" aria-label="Peer comparison table"><table className="stock-peer-table"><thead><tr>{['Company', 'Price', '1D Change', 'Market Cap', 'P/E Ratio'].map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{peers.map(peer => <tr key={peer.symbol}>
      <td><Link title={peer.name || peer.symbol} to={`/stock/${encodeURIComponent(peer.symbol)}`} onClick={() => window.scrollTo(0, 0)}><strong><span className="stock-peer-name">{peer.name || peer.symbol}</span><span className="stock-peer-symbol">{peer.baseSymbol || peer.symbol}</span></strong><small>{peer.baseSymbol || peer.symbol}</small></Link></td>
      <td>{money(peer.price)}</td><td><PriceChange value={peer.changePercent} badge /></td><td>{peer.marketCap == null ? '—' : `${money(peer.marketCap / 1e7)} Cr`}</td><td>{number(peer.peRatio)}</td>
    </tr>)}</tbody></table></div>}
  </div></section>
}
