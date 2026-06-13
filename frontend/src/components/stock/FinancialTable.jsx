import { useState } from 'react'

const FinancialTable = ({ title, unit, columns = [], rows = [] }) => {
  const [isOpen, setIsOpen] = useState(false)

  const visibleLimit = 3
  const isRatios = title === 'Ratios'
  const displayedColumns = isRatios ? columns : columns.slice(-visibleLimit)

  return (
    <>
      <div className="bg-[#14161c] border border-[#1f2129] rounded-lg p-3 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">{title}</h3>
              <p className="text-[9px] text-gray-500">{unit || 'Live provider data'}</p>
            </div>
            {columns.length > 0 && rows.length > 0 && (
              <button 
                onClick={() => setIsOpen(true)}
                className="text-[10px] font-semibold text-indigo-400 hover:text-indigo-300 px-1.5 py-0.5 rounded bg-indigo-500/10 transition-colors"
              >
                VIEW MORE
              </button>
            )}
          </div>

          {columns.length === 0 || rows.length === 0 ? (
            <div className="py-6 text-center text-[10px] text-gray-500">
              No live statement data available.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-[10px]">
                <thead>
                  <tr className="text-gray-500 border-b border-[#1f2129]">
                    <th className="text-left font-medium py-1"></th>
                    {displayedColumns.map((c) => (
                      <th key={c} className="text-right font-medium py-1 pl-2 whitespace-nowrap">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const displayedValues = isRatios ? row.values : row.values.slice(-visibleLimit)
                    return (
                      <tr key={row.label} className="border-b border-[#1f2129] last:border-0 hover:bg-[#181a21]/30">
                        <td className="py-1 text-gray-400 truncate max-w-[90px]" title={row.label}>
                          {row.label}
                        </td>
                        {displayedValues.map((v, i) => (
                          <td key={i} className="py-1 text-right text-gray-200 pl-2 whitespace-nowrap font-mono">
                            {v}
                          </td>
                        ))}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Popup Modal for complete values */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
          onClick={() => setIsOpen(false)}
        >
          <div 
            className="bg-[#0f1115] border border-[#1f2129] rounded-xl w-full max-w-3xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#1f2129] bg-[#14161c]">
              <div>
                <h3 className="text-base font-bold text-white">{title}</h3>
                <p className="text-xs text-gray-500">{unit || 'Figures in INR Crore'}</p>
              </div>
              <button 
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-white text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#1a1c23] border border-[#262833] transition-colors"
              >
                CLOSE
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto bg-[#0f1115]">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="text-gray-400 border-b border-[#1f2129]">
                    <th className="text-left font-semibold py-3 px-3">Metric</th>
                    {columns.map((c) => (
                      <th key={c} className="text-right font-semibold py-3 px-3">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.label} className="border-b border-[#1f2129] last:border-0 hover:bg-[#181a21]/50 transition-colors">
                      <td className="py-3 px-3 text-gray-300 font-medium">{row.label}</td>
                      {row.values.map((v, i) => (
                        <td key={i} className="py-3 px-3 text-right text-gray-100 font-mono">
                          {v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default FinancialTable
