import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { Star, Briefcase, Bell, ChevronDown, BarChart3, LogOut, User as UserIcon } from 'lucide-react'
import toast from 'react-hot-toast'

import SearchBar from './SearchBar'
import ThemeToggle from './ThemeToggle'
import { logout, selectUser } from '@/store/authSlice'

const Navbar = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const user = useSelector(selectUser)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    if (!menuOpen) return
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [menuOpen])

  const handleLogout = async () => {
    await dispatch(logout())
    toast.success('Signed out')
    navigate('/login', { replace: true })
  }

  const initial = (user?.name || user?.email || '?').charAt(0).toUpperCase()

  return (
    <header className="sticky top-0 z-40 border-b border-[#1f2129] bg-[#0d0e13]/95 backdrop-blur">
      <div className="mx-auto max-w-[1440px] px-6 h-14 flex items-center gap-6">
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <img src="/assest hunter.png" alt="Asset Hunter Logo" className="w-6 h-6 rounded object-contain" />
          <span className="font-semibold text-[15px] text-gray-100">Assest Hunter</span>
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

          {user ? (
            <div className="relative ml-1" ref={menuRef}>
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-pink-500 ring-2 ring-[#1f2129] text-sm font-semibold text-white overflow-hidden"
                title={user.email}
              >
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  initial
                )}
              </button>
              {menuOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-md border border-[#2a2d36] bg-[#15171c] shadow-lg py-1 text-sm">
                  <div className="px-3 py-2 border-b border-[#1f2129]">
                    <div className="font-medium text-gray-100 truncate">{user.name}</div>
                    <div className="text-xs text-gray-400 truncate">{user.email}</div>
                  </div>
                  <button
                    className="flex items-center w-full gap-2 px-3 py-2 text-gray-300 hover:bg-[#1a1c23]"
                    onClick={() => { setMenuOpen(false); navigate('/portfolio') }}
                  >
                    <UserIcon className="w-3.5 h-3.5" /> Profile
                  </button>
                  <button
                    className="flex items-center w-full gap-2 px-3 py-2 text-red-400 hover:bg-[#1a1c23]"
                    onClick={handleLogout}
                  >
                    <LogOut className="w-3.5 h-3.5" /> Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              to="/login"
              className="ml-2 px-3 py-1.5 rounded-md bg-indigo-500 hover:bg-indigo-400 text-white text-[13px] font-medium transition-colors"
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}

export default Navbar
