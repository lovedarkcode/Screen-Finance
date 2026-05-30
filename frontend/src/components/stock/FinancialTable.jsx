const FinancialTable = ({ title, columns, rows }) => {
  return (
    <div className="bg-[#14161c] border border-[#1f2129] rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-sm font-semibold text-white">{title}</h3>
          <p className="text-[10px] text-gray-500">Standalone Figures in $ Million</p>
        </div>
        <button className="text-[10px] font-medium text-indigo-400 hover:text-indigo-300">
          VIEW MORE →
        </button>
      </div>

      <table className="w-full text-[11px]">
        <thead>
          <tr className="text-gray-500 border-b border-[#1f2129]">
            <th className="text-left font-medium py-1.5"></th>
            {columns.map((c) => (
              <th key={c} className="text-right font-medium py-1.5">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-b border-[#1f2129] last:border-0">
              <td className="py-1.5 text-gray-400">{row.label}</td>
              {row.values.map((v, i) => (
                <td key={i} className="py-1.5 text-right text-gray-200">
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default FinancialTable
