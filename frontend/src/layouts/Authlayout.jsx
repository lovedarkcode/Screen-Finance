import { Link, Outlet } from 'react-router-dom'
import { BarChart3 } from 'lucide-react'

const Authlayout = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#0d0e13] text-gray-200">
      <header className="border-b border-[#1f2129]">
        <div className="mx-auto max-w-[1440px] px-6 h-14 flex items-center">
          <Link to="/" className="flex items-center gap-2">
            <img src="/assest hunter.png" alt="Asset Hunter Logo" className="w-6 h-6 rounded object-contain" />
            <span className="font-semibold text-[15px] text-gray-100">Assest Hunter</span>
          </Link>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <Outlet />
        </div>
      </main>

      <footer className="text-center text-xs text-gray-500 py-4">
        © {new Date().getFullYear()} Assest Hunter
      </footer>
    </div>
  )
}

export default Authlayout
