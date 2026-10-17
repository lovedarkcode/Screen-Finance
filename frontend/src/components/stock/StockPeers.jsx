import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table'
import { Link } from 'react-router-dom'
import { EmptyState, PriceChange, SectionTitle } from './StockUI'
import { money, number } from './stock-format'

export default function StockPeers({ peers = [], loading, error }) {
  return <section className="stock-section stock-band" id="peers"><div className="stock-container"><SectionTitle>Peer Comparison</SectionTitle>
    {loading ? <Skeleton className="sk sk-panel" /> : error ? <EmptyState error>Peer comparison is temporarily unavailable.</EmptyState> : !peers.length ? <EmptyState>No peers available</EmptyState> : <div className="stock-peer-scroll" tabIndex={0} role="region" aria-label="Peer comparison table"><Table className="stock-peer-table"><TableHeader><TableRow>{['Company', 'Price', '1D Change', 'Market Cap', 'P/E Ratio'].map(label => <TableHead key={label}>{label}</TableHead>)}</TableRow></TableHeader><TableBody>{peers.map(peer => <TableRow key={peer.symbol}>
      <TableCell><Link title={peer.name || peer.symbol} to={`/stock/${encodeURIComponent(peer.symbol)}`} onClick={() => window.scrollTo(0, 0)}><strong><span className="stock-peer-name">{peer.name || peer.symbol}</span><span className="stock-peer-symbol">{peer.baseSymbol || peer.symbol}</span></strong><small>{peer.baseSymbol || peer.symbol}</small></Link></TableCell>
      <TableCell>{money(peer.price)}</TableCell><TableCell><PriceChange value={peer.changePercent} badge /></TableCell><TableCell>{peer.marketCap == null ? '—' : `${money(peer.marketCap / 1e7)} Cr`}</TableCell><TableCell>{number(peer.peRatio)}</TableCell>
    </TableRow>)}</TableBody></Table></div>}
  </div></section>
}
