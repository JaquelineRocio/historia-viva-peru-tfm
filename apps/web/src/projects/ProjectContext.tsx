import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useProjects } from '../api/resources'
import type { HistoryProject } from '../types'

interface ProjectState {
  projects: HistoryProject[]
  project?: HistoryProject
  projectId: string
  setProjectId: (id: string) => void
}

const STORAGE_KEY = 'historia_viva_project'
const ProjectContext = createContext<ProjectState | undefined>(undefined)

export function ProjectProvider({ children }: { children: ReactNode }) {
  const query = useProjects()
  const projects = useMemo(() => query.data ?? [], [query.data])
  const [projectId, setProjectIdState] = useState(() => localStorage.getItem(STORAGE_KEY) || '')

  useEffect(() => {
    if (!projects.length) return
    if (!projects.some((item) => item.id === projectId)) {
      setProjectIdState(projects[0].id)
      localStorage.setItem(STORAGE_KEY, projects[0].id)
    }
  }, [projects, projectId])

  const value = useMemo(() => ({
    projects,
    projectId,
    project: projects.find((item) => item.id === projectId),
    setProjectId: (id: string) => {
      setProjectIdState(id)
      localStorage.setItem(STORAGE_KEY, id)
    },
  }), [projects, projectId])

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>
}

export function useActiveProject() {
  const context = useContext(ProjectContext)
  if (!context) throw new Error('useActiveProject debe usarse dentro de ProjectProvider')
  return context
}
