import { Link } from 'react-router-dom'

const tools = [
  { to: '/fuentes', title: 'Fuentes y PDF', text: 'Gestiona videos y documentos, el corpus y su publicación.' },
  { to: '/revision', title: 'Revisión', text: 'Revisa por lotes los subtemas de los fragmentos.' },
  { to: '/buscar', title: 'Búsqueda de evidencia', text: 'Busca por texto, personajes, lugares y años.' },
  { to: '/colecciones', title: 'Colecciones', text: 'Agrupa fragmentos citables con notas.' },
  { to: '/proyectos', title: 'Proyectos', text: 'Crea y cambia de proyecto de investigación.' },
  { to: '/administracion', title: 'Publicaciones', text: 'Aprueba o rechaza solicitudes de publicación.' },
  { to: '/datasets', title: 'Datasets', text: 'Crea snapshots inmutables de etiquetas revisadas.' },
  { to: '/entrenar', title: 'Entrenamiento', text: 'Fine-tunea BETO o prepara un entrenamiento en Colab.' },
  { to: '/versiones', title: 'Versiones', text: 'Compara métricas y activa el mejor modelo.' },
  { to: '/clasificar', title: 'Clasificación', text: 'Prueba el modelo activo y corrige sus predicciones.' },
  { to: '/ingesta-anterior', title: 'Flujo anterior', text: 'Accede a los videos creados antes de Historia Viva.' },
]

export function LabPage() {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Área avanzada</p>
      <h1 className="text-2xl font-bold">Laboratorio</h1>
      <p className="mt-1 max-w-2xl text-sm text-slate-500">Herramientas técnicas para gestionar fuentes, preparar datos, entrenar BETO y evaluar versiones. El docente no las necesita: le bastan «Mis videos» y «Por subtema».</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => (
          <Link key={tool.to} to={tool.to} className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-md">
            <span className="text-sm font-bold text-indigo-700">{tool.title}</span>
            <p className="mt-2 text-sm leading-6 text-slate-600">{tool.text}</p>
            <span className="mt-4 inline-block text-xs font-semibold text-indigo-600">Abrir herramienta →</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
