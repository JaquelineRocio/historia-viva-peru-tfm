import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useActiveProject } from '../projects/ProjectContext'

export function Layout() {
  const { user, logout } = useAuth()
  const { projects, projectId, setProjectId } = useActiveProject()
  const advanced = user?.role === 'curador' || user?.role === 'admin'
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `whitespace-nowrap rounded-xl px-3 py-2 text-sm font-semibold transition ${
      isActive ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
    }`

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3 sm:gap-5">
            <NavLink to="/" className="flex shrink-0 items-center gap-2" aria-label="Historia Viva Perú">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-600 font-serif text-lg font-bold text-white">H</span>
              <span className="hidden font-bold text-slate-900 md:block">Historia Viva <span className="text-indigo-600">Perú</span></span>
            </NavLink>
            <nav className="flex gap-1 overflow-x-auto">
              <NavLink to="/" className={linkCls} end>Mis videos</NavLink>
              <NavLink to="/subtemas" className={linkCls}>Por subtema</NavLink>
              {advanced && <NavLink to="/laboratorio" className={linkCls}>Laboratorio</NavLink>}
            </nav>
          </div>
          <div className="flex shrink-0 items-center gap-3 text-sm">
            {advanced && projects.length > 1 && (
              <select aria-label="Proyecto activo" value={projectId} onChange={(event) => setProjectId(event.target.value)} className="hidden max-w-56 rounded-xl border border-slate-200 px-3 py-2 text-xs lg:block">
                {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
              </select>
            )}
            <span className="hidden text-slate-500 lg:inline">{user?.displayName ?? user?.username}</span>
            <button onClick={logout} className="rounded-xl border border-slate-300 px-3 py-2 hover:bg-slate-100">Salir</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}
