# Guion del vídeo TFM — 7 a 9 minutos

## Preparación

- Use una ventana limpia a 1440×900 o 1920×1080 y zoom del navegador al 100%.
- Inicie sesión antes de grabar y mantenga abierta una fuente ya procesada.
- Prepare un PDF pequeño y un YouTube con subtítulos para evitar tiempos muertos.
- Muestre su rostro o voz según las normas del máster; la autora debe realizar la
  grabación.

## Guion

### 0:00–0:45 — Presentación y problema

“Soy Jaqueline Ramos. Historia Viva Perú reduce el tiempo que un docente necesita
para localizar y citar evidencia dentro de videos y documentos históricos.”

### 0:45–1:25 — Propuesta y alcance

Explique el periodo 1780–1842 y el flujo fuente → segmentos → entidades → BETO →
corrección. Aclare que BETO sugiere, no sustituye el criterio docente.

### 1:25–2:00 — Arquitectura

Muestre una diapositiva: React en Vercel, NestJS en Render,
PostgreSQL/pgvector en Neon, archivos en Supabase Storage, FastAPI/BETO en Modal y
pesos del modelo en Hugging Face Hub. Destaque trazabilidad por página o minuto.

### 2:00–2:35 — Login y proyecto

Ingrese con `docente / tfm2026`, enseñe el selector global y explique que la cuenta
de demo es colaboradora, no administradora.

### 2:35–3:30 — Añadir fuente

Abra **Fuentes**, añada la URL o PDF, confirme la declaración académica y pulse
**Añadir y procesar**. Explique brevemente que YouTube usa subtítulos directos,
Supadata si la plataforma bloquea la IP remota y Whisper como último fallback.
Pase a una fuente ya lista para evitar esperar durante la grabación.

### 3:30–4:40 — Segmentos enriquecidos

Muestre texto, subtítulo temático, confianza, timestamp/página, años, personajes y
lugares. Abra el segundo o página exactos.

### 4:40–5:35 — Corrección docente

En **Revisión**, filtre baja confianza, cambie una etiqueta y confirme otra.
Explique que el feedback entra a curación y no reentrena el modelo al instante.

### 5:35–6:25 — Búsqueda verificable

Busque una pregunta válida y abra una evidencia. Luego pregunte “¿Qué relación tuvo
Apolo 11 con la Independencia peruana?” y muestre la abstención obligatoria.

### 6:25–7:15 — Dataset y resultados

Muestre el snapshot de 814 segmentos procedentes de 10 fuentes, con split por
fuente, y los resultados: TF-IDF 0.353, BETO 0.425 y Kappa 0.651. Aclare que el
corte inicial procesó 11 fuentes, pero el snapshot reproducible representa 10.
Diga explícitamente que BETO es experimental.

### 7:15–8:00 — Limitaciones y cierre

Mencione ausencia de historiador independiente, sin OCR, periodo limitado,
servicios gratuitos y licencia no verificable. Cierre con el valor docente y el
trabajo futuro: corpus mayor, validación experta, BETO v2 y pruebas con docentes.

## Después de grabar

1. Suba a YouTube no listado o Drive público.
2. Compruebe el enlace sin iniciar sesión.
3. Sustituya `PENDIENTE_URL_VIDEO` en README.
