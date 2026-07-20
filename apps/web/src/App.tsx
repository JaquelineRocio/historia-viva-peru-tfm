import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { Layout } from './components/Layout'
import { ClassifyPage } from './pages/ClassifyPage'
import { DatasetPage } from './pages/DatasetPage'
import { IngestPage } from './pages/IngestPage'
import { LabelingPage } from './pages/LabelingPage'
import { LoginPage } from './pages/LoginPage'
import { TrainingPage } from './pages/TrainingPage'
import { VersionsPage } from './pages/VersionsPage'
import { HomePage } from './pages/HomePage'
import { ProjectsPage } from './pages/ProjectsPage'
import { SourcesPage } from './pages/SourcesPage'
import { ReviewPage } from './pages/ReviewPage'
import { SearchPage } from './pages/SearchPage'
import { CollectionsPage } from './pages/CollectionsPage'
import { LabPage } from './pages/LabPage'
import { AdminPage } from './pages/AdminPage'
import { PublicExplorePage } from './pages/PublicExplorePage'
import { ProjectProvider } from './projects/ProjectContext'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/explorar" element={<PublicExplorePage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<ProjectProvider><Layout /></ProjectProvider>}>
              <Route path="/" element={<HomePage />} />
              <Route path="/proyectos" element={<ProjectsPage />} />
              <Route path="/fuentes" element={<SourcesPage />} />
              <Route path="/revision" element={<ReviewPage />} />
              <Route path="/buscar" element={<SearchPage />} />
              <Route path="/colecciones" element={<CollectionsPage />} />
              <Route path="/laboratorio" element={<LabPage />} />
              <Route path="/administracion" element={<AdminPage />} />
              <Route path="/ingesta-anterior" element={<IngestPage />} />
              <Route path="/etiquetar" element={<LabelingPage />} />
              <Route path="/datasets" element={<DatasetPage />} />
              <Route path="/entrenar" element={<TrainingPage />} />
              <Route path="/versiones" element={<VersionsPage />} />
              <Route path="/clasificar" element={<ClassifyPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
