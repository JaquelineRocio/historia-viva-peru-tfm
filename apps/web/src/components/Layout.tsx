import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useActiveProject } from '../projects/ProjectContext'

export function Layout() {
  const { user, logout } = useAuth()
  const { projects, projectId, setProjectId } = useActiveProject()
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `whitespace-nowrap rounded-xl px-3 py-2 text-sm font-medium transition ${
      isActive ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
    }`

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex min-w-0 items-center gap-5">
            <NavLink to="/" className="flex shrink-0 items-center gap-2">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-600 font-serif text-lg font-bold text-white">H</span>
              <span className="hidden font-bold text-slate-900 sm:block">Historia Viva <span className="text-indigo-600">Perú</span></span>
            </NavLink>
            <nav className="flex gap-1 overflow-x-auto">
              <NavLink to="/" className={linkCls} end>Inicio</NavLink>
              <NavLink to="/proyectos" className={linkCls}>Proyectos</NavLink>
              <NavLink to="/fuentes" className={linkCls}>Fuentes</NavLink>
              <NavLink to="/revision" className={linkCls}>Revisión</NavLink>
              <NavLink to="/colecciones" className={linkCls}>Colecciones</NavLink>
              <NavLink to="/laboratorio" className={linkCls}>Laboratorio</NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {projects.length > 0 && (
              <select aria-label="Proyecto activo" value={projectId} onChange={(event) => setProjectId(event.target.value)} className="hidden max-w-56 rounded-xl border border-slate-200 px-3 py-2 text-xs md:block">
                {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
              </select>
            )}
            <span className="text-slate-500">{user?.displayName ?? user?.username}</span>
            <NavLink to="/buscar" className="hidden rounded-xl bg-violet-100 px-3 py-2 font-semibold text-violet-700 lg:block">Buscar</NavLink>
            {(user?.role === 'curador' || user?.role === 'admin') && <NavLink to="/administracion" className="hidden text-xs font-semibold text-slate-500 xl:block">Administrar</NavLink>}
            <button onClick={logout} className="rounded-xl border border-slate-300 px-3 py-2 hover:bg-slate-100">
              Salir
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
