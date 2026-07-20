# Web React — Historia Viva Perú

Interfaz docente construida con React 19, TypeScript y Vite. Incluye proyectos,
fuentes PDF/YouTube, segmentos enriquecidos, revisión, búsqueda verificable,
colecciones, exploración pública y laboratorio de modelos.

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
