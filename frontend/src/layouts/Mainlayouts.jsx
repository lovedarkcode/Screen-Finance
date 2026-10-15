import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '@/components/common/Navbar'

const Mainlayouts = () => {
  const { pathname } = useLocation()
  if (pathname.startsWith('/stock/')) return <Outlet />
  return (
    <div className="min-h-screen bg-[#0d0e13] text-gray-200">
      <Navbar />
      <main className="px-6 py-4 mx-auto max-w-[1440px]">
        <Outlet />
      </main>
    </div>
  )
}

export default Mainlayouts
