const NewsCard = ({ about, related = [] }) => {
  const website = about?.website && about.website !== 'N/A' ? about.website : ''

  return (
    <>
      <div className="bg-[#14161c] border border-[#1f2129] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-2">About</h3>
        <p className="text-[12px] text-gray-400 leading-relaxed">
          {about?.description || 'Company profile is not available from the live data provider.'}
        </p>

        <div className="mt-4 space-y-2 text-[12px]">
          <div className="flex justify-between">
            <span className="text-gray-500">Founded</span>
            <span className="text-gray-200">{about?.founded || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Headquarters</span>
            <span className="text-gray-200 text-right">{about?.headquarters || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Website</span>
            {website ? (
              <a
                href={`https://${website}`}
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 hover:text-indigo-300"
              >
                {website}
              </a>
            ) : (
              <span className="text-gray-200">N/A</span>
            )}
          </div>
        </div>

        <button className="w-full mt-4 py-2 text-[11px] font-semibold text-indigo-300 border border-indigo-500/30 rounded-md hover:bg-indigo-500/10">
          VIEW COMPANY PROFILE
        </button>
      </div>

      <div className="bg-[#14161c] border border-[#1f2129] rounded-lg p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Related Stocks</h3>
        {related.length === 0 ? (
          <div className="py-4 text-[12px] text-gray-500">No live peers returned by provider.</div>
        ) : (
          <div className="space-y-3">
            {related.map((s) => {
              const positive = Number(s.changePercent || 0) >= 0
              const price = Number(s.price || 0)
              return (
                <div key={s.symbol} className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-[12px] font-medium text-gray-200">{s.name}</p>
                    <p className="text-[10px] text-gray-500">{s.symbol}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[12px] font-medium text-gray-200">
                      {s.currencySymbol || 'INR'} {price ? price.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : 'N/A'}
                    </p>
                    <p
                      className={`text-[10px] font-medium ${
                        positive ? 'text-emerald-400' : 'text-red-400'
                      }`}
                    >
                      {positive ? 'UP' : 'DOWN'} {Math.abs(Number(s.changePercent || 0)).toFixed(2)}%
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        )}
        <button className="w-full mt-3 text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 text-right">
          VIEW MORE
        </button>
      </div>
    </>
  )
}

export default NewsCard
