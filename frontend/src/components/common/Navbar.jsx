import { Link } from 'react-router-dom'
import { Star, Briefcase, Bell, ChevronDown, BarChart3 } from 'lucide-react'
import SearchBar from './SearchBar'
import ThemeToggle from './ThemeToggle'

const Navbar = () => {
  return (
    <header className="sticky top-0 z-40 border-b border-[#1f2129] bg-[#0d0e13]/95 backdrop-blur">
      <div className="mx-auto max-w-[1440px] px-6 h-14 flex items-center gap-6">
        <Link to="/" className="flex items-center gap-1.5 shrink-0">
          <span className="font-semibold text-[15px] text-gray-100">StockScreener</span>
          <BarChart3 className="w-4 h-4 text-indigo-400" />
        </Link>

        <nav className="flex items-center gap-5 text-[13px] font-medium text-gray-300">
          <Link to="/feed" className="hover:text-white transition-colors">FEED</Link>
          <Link to="/screens" className="hover:text-white transition-colors">SCREENS</Link>
          <button className="flex items-center gap-1 hover:text-white transition-colors">
            TOOLS <ChevronDown className="w-3 h-3" />
          </button>
        </nav>

        <SearchBar />

        <div className="flex items-center gap-1 shrink-0">
          <ThemeToggle />
          <Link
            to="/watchlist"
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-[13px] text-gray-300 hover:text-white hover:bg-[#1a1c23] rounded-md transition-colors"
          >
            <Star className="w-3.5 h-3.5" />
            Watchlist
          </Link>
          <Link
            to="/portfolio"
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-[13px] text-gray-300 hover:text-white hover:bg-[#1a1c23] rounded-md transition-colors"
          >
            <Briefcase className="w-3.5 h-3.5" />
            Portfolio
          </Link>
          <button className="relative p-2 text-gray-400 hover:text-gray-200 hover:bg-[#1a1c23] rounded-md transition-colors">
            <Bell className="w-4 h-4" />
            <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full" />
          </button>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-pink-500 ml-1 ring-2 ring-[#1f2129]" />
        </div>
      </div>
    </header>
  )
}

export default Navbar
