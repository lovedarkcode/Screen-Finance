import MetricsCard from '@/components/stock/MetricsCard'
import StockChart from '@/components/stock/StockChart'

const Overview = ({ metrics = [], chartData = [], stock }) => {
  const cols = [
    metrics.filter((_, i) => i % 3 === 0),
    metrics.filter((_, i) => i % 3 === 1),
    metrics.filter((_, i) => i % 3 === 2),
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
        {metrics.length === 0 && (
          <div className="px-3 py-8 text-center text-[12px] text-gray-500">
            Live metrics are not available for this stock.
          </div>
        )}

      </div>

      <StockChart symbol={stock?.symbol} currency={stock?.currency} timeZone={stock?.timeZone} initialData={chartData} />
    </section>
  )
}

export default Overview
