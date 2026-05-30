import { useState } from 'react'
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { ChevronDown, TriangleAlert } from 'lucide-react'

const RANGES = ['1M', '6M', '1Yr', '3Yr', '5Yr', '10Yr', 'Max']

const StockChart = ({ data }) => {
  const [range, setRange] = useState('1Yr')
  const [showPrice, setShowPrice] = useState(true)
  const [showVolume, setShowVolume] = useState(true)

  return (
    <div className="bg-[#14161c] border border-[#1f2129] rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1 bg-[#1a1c23] rounded-md p-0.5">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-2 py-1 text-[11px] font-medium rounded transition-colors ${
                range === r
                  ? 'bg-[#262833] text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1 text-[11px]">
          <button className="px-2 py-1 bg-[#1a1c23] rounded text-gray-200 border border-[#262833]">
            Price
          </button>
          <button className="px-2 py-1 text-gray-400 hover:text-gray-200">PE Ratio</button>
          <button className="flex items-center gap-1 px-2 py-1 text-gray-400 hover:text-gray-200">
            More <ChevronDown className="w-3 h-3" />
          </button>
          <button className="flex items-center gap-1 px-2 py-1 text-amber-400">
            <TriangleAlert className="w-3 h-3" /> Alerts
          </button>
        </div>
      </div>

      <div className="h-[230px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 5, bottom: 0, left: -10 }}>
            <CartesianGrid stroke="#1f2129" strokeDasharray="2 4" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              axisLine={{ stroke: '#1f2129' }}
              tickLine={false}
            />
            <YAxis
              yAxisId="price"
              orientation="right"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              domain={['dataMin - 10', 'dataMax + 5']}
            />
            <YAxis
              yAxisId="volume"
              orientation="left"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v / 1_000_000}M`}
            />
            <Tooltip
              contentStyle={{
                background: '#1a1c23',
                border: '1px solid #262833',
                borderRadius: 6,
                fontSize: 12,
              }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            {showVolume && (
              <Bar
                yAxisId="volume"
                dataKey="volume"
                fill="#2a2d36"
                barSize={10}
                radius={[2, 2, 0, 0]}
              />
            )}
            {showPrice && (
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="price"
                stroke="#818cf8"
                strokeWidth={2}
                dot={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-4 mt-2 text-[11px] text-gray-400">
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={showPrice}
            onChange={(e) => setShowPrice(e.target.checked)}
            className="w-3 h-3 accent-indigo-500"
          />
          Price on NASDAQ
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={showVolume}
            onChange={(e) => setShowVolume(e.target.checked)}
            className="w-3 h-3 accent-gray-400"
          />
          Volume
        </label>
      </div>
    </div>
  )
}

export default StockChart
