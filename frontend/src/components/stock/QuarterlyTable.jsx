import { Button } from '@/components/ui/button'
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table'
import { FileText } from 'lucide-react'

const QuarterlyTable = ({ quarters = { columns: [], rows: [] } }) => {
  const columns = quarters.columns || []
  const rows = quarters.rows || []

  return (
    <section className="bg-[#14161c] border border-[#1f2129] rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1f2129]">
        <div>
          <h2 className="text-base font-semibold text-white">{quarters.title || 'Quarterly Results'}</h2>
          <p className="text-[11px] text-gray-500">{quarters.unit || 'Live provider data'}</p>
        </div>
        <Button variant="ghost" size="sm" className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300">
          VIEW CONSOLIDATED
        </Button>
      </div>

      {columns.length === 0 || rows.length === 0 ? (
        <div className="px-4 py-8 text-center text-[12px] text-gray-500">
          No live quarterly result data available.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <Table className="w-full text-[12px]">
            <TableHeader>
              <TableRow className="text-gray-400 border-b border-[#1f2129]">
                <TableHead className="text-left font-medium py-2 px-4 sticky left-0 bg-[#14161c]"></TableHead>
                {columns.map((c) => (
                  <TableHead key={c} className="text-right font-medium py-2 px-3 whitespace-nowrap">
                    {c}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow
                  key={row.label}
                  className="border-b border-[#1f2129] last:border-0 hover:bg-[#181a21]"
                >
                  <TableCell className="py-2 px-4 text-gray-300 sticky left-0 bg-[#14161c]">{row.label}</TableCell>
                  {row.values.map((v, i) => (
                    <TableCell key={i} className="py-2 px-3 text-right text-gray-200 whitespace-nowrap">
                      {v}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
              <TableRow className="hover:bg-[#181a21]">
                <TableCell className="py-2 px-4 text-gray-300 sticky left-0 bg-[#14161c]">Source document</TableCell>
                {columns.map((c) => (
                  <TableCell key={c} className="py-2 px-3 text-right">
                    <FileText className="w-3.5 h-3.5 text-gray-500 inline" />
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  )
}

export default QuarterlyTable
