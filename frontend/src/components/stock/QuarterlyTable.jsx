import { FileText } from 'lucide-react'

const QuarterlyTable = ({ quarters }) => {
  const columns = quarters.columns
  const rows = quarters.rows

  return (
    <section className="bg-[#14161c] border border-[#1f2129] rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1f2129]">
        <div>
          <h2 className="text-base font-semibold text-white">Quarterly Results</h2>
          <p className="text-[11px] text-gray-500">Standalone Figures in $ Million</p>
        </div>
        <button className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300">
          VIEW CONSOLIDATED →
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="text-gray-400 border-b border-[#1f2129]">
              <th className="text-left font-medium py-2 px-4 sticky left-0 bg-[#14161c]"></th>
              {columns.map((c) => (
                <th key={c} className="text-right font-medium py-2 px-3 whitespace-nowrap">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.label}
                className="border-b border-[#1f2129] last:border-0 hover:bg-[#181a21]"
              >
                <td className="py-2 px-4 text-gray-300 sticky left-0 bg-[#14161c]">{row.label}</td>
                {row.values.map((v, i) => (
                  <td key={i} className="py-2 px-3 text-right text-gray-200 whitespace-nowrap">
                    {v}
                  </td>
                ))}
              </tr>
            ))}
            <tr className="hover:bg-[#181a21]">
              <td className="py-2 px-4 text-gray-300 sticky left-0 bg-[#14161c]">View PDF</td>
              {columns.map((c) => (
                <td key={c} className="py-2 px-3 text-right">
                  <FileText className="w-3.5 h-3.5 text-gray-500 inline" />
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default QuarterlyTable
