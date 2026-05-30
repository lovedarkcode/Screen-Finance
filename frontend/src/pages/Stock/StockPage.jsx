import { useState } from 'react'
import StockHeader from '@/components/stock/StockHeader'
import QuarterlyTable from '@/components/stock/QuarterlyTable'
import FinancialTable from '@/components/stock/FinancialTable'
import AIInsightCard from '@/components/stock/AIInsightCard'
import NewsCard from '@/components/stock/NewsCard'
import Overview from './Overview'
import {
  mockStock,
  mockQuarters,
  mockSummaryTables,
  mockAISummary,
  mockAbout,
  mockRelated,
} from '@/services/stock.service'

const TABS = [
  'Overview', 'Chart', 'Analysis', 'Peers', 'Quarters',
  'Profit & Loss', 'Balance Sheet', 'Cash Flow', 'Ratios',
  'Investors', 'Documents', 'AI Summary',
]

const StockPage = () => {
  const [active, setActive] = useState('Overview')

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-4">
      <div>
        <StockHeader stock={mockStock} />

        <div className="border-b border-[#1f2129] mb-4">
          <nav className="flex items-center gap-5 text-[12px] overflow-x-auto">
            {TABS.map((t) => {
              const isActive = active === t
              return (
                <button
                  key={t}
                  onClick={() => setActive(t)}
                  className={`relative pb-2 whitespace-nowrap transition-colors ${
                    isActive
                      ? 'text-indigo-400 font-medium'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    {t}
                    {t === 'AI Summary' && (
                      <span className="text-[8px] font-semibold px-1 py-0.5 bg-indigo-500/20 text-indigo-300 rounded">
                        NEW
                      </span>
                    )}
                  </span>
                  {isActive && (
                    <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-indigo-400" />
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        <Overview />

        <div className="mt-4">
          <QuarterlyTable quarters={mockQuarters} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mt-4">
          <FinancialTable {...mockSummaryTables.profitLoss} />
          <FinancialTable {...mockSummaryTables.balanceSheet} />
          <FinancialTable {...mockSummaryTables.cashFlow} />
          <FinancialTable {...mockSummaryTables.ratios} />
        </div>
      </div>

      <aside className="flex flex-col gap-3">
        <AIInsightCard summary={mockAISummary.summary} keyPoints={mockAISummary.keyPoints} />
        <NewsCard about={mockAbout} related={mockRelated} />
      </aside>
    </div>
  )
}

export default StockPage
