const MetricsCard = ({ label, value, valueClassName = '' }) => {
  return (
    <div className="flex items-center justify-between py-2.5 px-3 border-b border-[#1f2129]">
      <span className="text-[12px] text-gray-400">{label}</span>
      <span className={`text-[13px] font-medium text-gray-100 ${valueClassName}`}>{value}</span>
    </div>
  )
}

export default MetricsCard
