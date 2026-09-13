import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

/** Envuelve las rutas privadas: sin usuario → /login. */
export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="p-8 text-slate-500">Cargando…</div>
  if (!user) return <Navigate to="/login" state={{ returnTo: location.pathname }} replace />
  return <Outlet />
}
