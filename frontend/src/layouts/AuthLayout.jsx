import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24 }}>
      <Outlet />
    </main>
  )
}
