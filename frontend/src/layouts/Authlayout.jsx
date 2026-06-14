import { Link, Outlet } from 'react-router-dom'

const Authlayout = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#0d0e13] text-gray-200">
      <header className="border-b border-[#1f2129]">
        <div className="mx-auto max-w-[1440px] px-6 h-14 flex items-center">
          <Link to="/" className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-md bg-white border border-[#2a2d36] overflow-hidden flex items-center justify-center">
              <img
                src="/assest-hunter.png"
                alt="Asset Hunter Logo"
                className="w-full h-full object-cover scale-[2.8]"
                style={{ objectPosition: '50% 34%' }}
              />
            </span>
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
