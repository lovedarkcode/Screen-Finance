import { Button } from '@/components/ui/button'
const AIInsightCard = ({ summary, keyPoints }) => {
  return (
    <div className="bg-[#14161c] border border-[#1f2129] rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold text-white">AI Summary</h3>
        <span className="text-[9px] font-semibold px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded">
          NEW
        </span>
      </div>
      <p className="text-[12px] text-gray-400 leading-relaxed">{summary}</p>
      <Button variant="ghost" size="sm" className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 mt-2">
        READ MORE →
      </Button>

      <div className="mt-5">
        <h4 className="text-sm font-semibold text-white mb-2">Key Points</h4>
        <ul className="space-y-1.5">
          {keyPoints.map((point, i) => (
            <li key={i} className="flex gap-2 text-[12px] text-gray-400 leading-relaxed">
              <span className="text-indigo-400 mt-1.5 w-1 h-1 rounded-full bg-indigo-400 shrink-0" />
              {point}
            </li>
          ))}
        </ul>
        <Button variant="ghost" size="sm" className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 mt-2">
          READ MORE →
        </Button>
      </div>
    </div>
  )
}

export default AIInsightCard
