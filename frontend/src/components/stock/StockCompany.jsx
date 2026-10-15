import { useState } from 'react'
import { Building2, Calendar, ChevronDown, ExternalLink, Globe, User } from 'lucide-react'
import { EmptyState, SectionTitle } from './StockUI'

export default function StockCompany({ stock, about, loading, error }) {
  const [expanded, setExpanded] = useState(false)
  let website = null
  try { const parsed = new URL(about?.website); if (['https:', 'http:'].includes(parsed.protocol)) website = parsed } catch { /* Provider URL unavailable. */ }
  const facts = [
    [Building2, 'Headquarters', about?.headquarters || '—'],
    [Calendar, 'Year of Incorporation', about?.founded || '—'],
    [User, 'MD / CEO', about?.ceo || '—'],
    [Globe, 'Website', website ? <a href={website.href} target="_blank" rel="noreferrer">{website.hostname}<ExternalLink size={10} /></a> : '—'],
  ]
  return <section className="stock-section" id="about"><div className="stock-container"><SectionTitle>About {stock.name}</SectionTitle>
    {loading ? <div className="sk sk-card" /> : error ? <EmptyState error>Company profile is temporarily unavailable.</EmptyState> : <>
      {about?.description ? <><p className={`stock-about-description ${expanded ? 'is-expanded' : ''}`}>{about.description}</p><button className="stock-read-more" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? 'Show less' : 'Read more'}<ChevronDown size={12} style={{ transform: expanded ? 'rotate(180deg)' : undefined }} /></button></> : <p className="stock-source-note">Company description is unavailable from the provider.</p>}
      <div className="stock-facts">{facts.map(([Icon, label, value]) => <div key={label}><Icon size={15} /><span><small>{label}</small><strong>{value}</strong></span></div>)}</div>
    </>}
  </div></section>
}
