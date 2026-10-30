# Web React — Historia Viva Perú

Interfaz docente construida con React 19, TypeScript y Vite. El docente usa dos
pantallas, que siguen el flujo de indexación temática asistida de la tesis:

- **Mis videos** (`/`, `/videos/:id`): pega un enlace de YouTube; cada fragmento
  muestra su minuto, la transcripción y sus dos subtemas más probables. Los no
  relevantes se ocultan, los de confianza ≥ 0,6 se etiquetan solos y el resto se
  confirma o corrige con un clic (reglas en `src/lib/indexing.ts`).
- **Por subtema** (`/subtemas`): reúne los fragmentos de un subtema de todos los videos.

Las herramientas técnicas (fuentes PDF, revisión por lotes, búsqueda, colecciones,
datasets, entrenamiento y versiones) se abren desde **Laboratorio**, visible solo
para curadores y administradores.

## Ejecución

```powershell
npm ci --include=optional
npm run dev
```

Configure `VITE_API_URL=http://localhost:3000/api` para desarrollo o la URL HTTPS
de Render para producción. Vercel usa `vercel.json` para resolver las rutas SPA.

## Calidad

```powershell
npm run lint
npm run build
```

Estado verificado: lint sin errores y build de producción correcto. Vite advierte
que el bundle principal supera 500 kB; es una mejora de rendimiento pendiente,
no un fallo funcional.
