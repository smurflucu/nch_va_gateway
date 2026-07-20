import { Outlet } from 'react-router-dom'
import Topbar from '@/components/common/Navbar'
import Sidebar from '@/components/common/Sidebar'
import { useAuthStore } from '@/features/auth'

export default function MainLayout() {
  const user = useAuthStore((s) => s.user)

  // Belum login → tampilkan konten polos (mis. HomePage / login redirect)
  if (!user) {
    return (
      <main style={{ maxWidth: 960, margin: '0 auto', padding: 28 }}>
        <Outlet />
      </main>
    )
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Topbar />
        <main style={{ flex: 1, padding: '24px 28px', maxWidth: 1280, width: '100%', margin: '0 auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
