import { Pencil } from 'lucide-react'
import MetricsCard from '@/components/stock/MetricsCard'
import StockChart from '@/components/stock/StockChart'
import { mockMetrics, mockChartData } from '@/services/stock.service'

const Overview = () => {
  const cols = [
    mockMetrics.filter((_, i) => i % 3 === 0),
    mockMetrics.filter((_, i) => i % 3 === 1),
    mockMetrics.filter((_, i) => i % 3 === 2),
  ]

  return (
    <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="bg-[#14161c] border border-[#1f2129] rounded-lg p-2">
        <div className="grid grid-cols-3 gap-x-2">
          {cols.map((col, ci) => (
            <div key={ci}>
              {col.map((m) => (
                <MetricsCard key={m.label} label={m.label} value={m.value} />
              ))}
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between gap-3 px-3 py-2 mt-2 border border-dashed border-[#262833] rounded-md">
          <div className="flex-1">
            <p className="text-[11px] text-gray-500 mb-1">Add ratio to table</p>
            <input
              type="text"
              placeholder="eg. Promoter holding"
              className="w-full bg-transparent text-[12px] text-gray-300 placeholder-gray-600 focus:outline-none"
            />
          </div>
          <button className="flex items-center gap-1 text-[11px] font-medium text-indigo-400 hover:text-indigo-300 whitespace-nowrap">
            <Pencil className="w-3 h-3" /> EDIT RATIOS
          </button>
        </div>
      </div>

      <StockChart data={mockChartData} />
    </section>
  )
}

export default Overview
