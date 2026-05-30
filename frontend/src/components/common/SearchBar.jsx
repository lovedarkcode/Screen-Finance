import { Search } from 'lucide-react'

const SearchBar = () => {
  return (
    <div className="relative flex-1 max-w-xl">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
      <input
        type="text"
        placeholder="Search for a company, sector or metric..."
        className="w-full pl-9 pr-10 py-2 text-sm bg-[#1a1c23] border border-[#262833] rounded-md text-gray-300 placeholder-gray-500 focus:outline-none focus:border-indigo-500/60"
      />
      <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-gray-500 border border-[#33363f] rounded px-1.5 py-0.5">
        /
      </kbd>
    </div>
  )
}

export default SearchBar
