import { Routes, Route, Navigate } from 'react-router-dom'
import { ROUTES } from '@/config/routes'
import MainLayout from '@/layouts/MainLayout'
import AuthLayout from '@/layouts/AuthLayout'
import HomePage from '@/pages/HomePage'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import JobsPage from '@/pages/JobsPage'
import SessionsPage from '@/pages/SessionsPage'
import SendPage from '@/pages/SendPage'
import ContactsPage from '@/pages/ContactsPage'
import TemplatesPage from '@/pages/TemplatesPage'
import BroadcastPage from '@/pages/BroadcastPage'
import InboxPage from '@/pages/InboxPage'
import AutoRepliesPage from '@/pages/AutoRepliesPage'
import ApiKeysPage from '@/pages/ApiKeysPage'
import TeamPage from '@/pages/TeamPage'
import { useAuthStore, useRestoreSession } from '@/features/auth'

function ProtectedRoute({ children, roles }) {
  const user = useAuthStore((s) => s.user)
  const initialized = useAuthStore((s) => s.initialized)
  if (!initialized) return <p style={{ padding: 24 }}>Memuat…</p>
  if (!user) return <Navigate to={ROUTES.login} replace />
  if (roles && !roles.includes(user.role)) return <Navigate to={ROUTES.dashboard} replace />
  return children
}

const guard = (el) => <ProtectedRoute>{el}</ProtectedRoute>
const roleGuard = (el, roles) => <ProtectedRoute roles={roles}>{el}</ProtectedRoute>

export default function App() {
  useRestoreSession()
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path={ROUTES.home} element={<HomePage />} />
        <Route path={ROUTES.dashboard} element={guard(<DashboardPage />)} />
        <Route path={ROUTES.team} element={roleGuard(<TeamPage />, ['admin', 'supervisor'])} />
        <Route path={ROUTES.jobs} element={roleGuard(<JobsPage />, ['admin'])} />
        <Route path={ROUTES.sessions} element={guard(<SessionsPage />)} />
        <Route path={ROUTES.send} element={guard(<SendPage />)} />
        <Route path={ROUTES.contacts} element={guard(<ContactsPage />)} />
        <Route path={ROUTES.templates} element={guard(<TemplatesPage />)} />
        <Route path={ROUTES.broadcast} element={guard(<BroadcastPage />)} />
        <Route path={ROUTES.inbox} element={guard(<InboxPage />)} />
        <Route path={ROUTES.autoreplies} element={roleGuard(<AutoRepliesPage />, ['admin', 'supervisor'])} />
        <Route path={ROUTES.apikeys} element={roleGuard(<ApiKeysPage />, ['admin'])} />
      </Route>
      <Route element={<AuthLayout />}>
        <Route path={ROUTES.login} element={<LoginPage />} />
      </Route>
    </Routes>
  )
}
