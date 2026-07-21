# Arquitectura actual — Historia Viva Perú

## Propósito

Historia Viva Perú permite incorporar PDF textuales y videos de YouTube sobre
1780–1842, convertirlos en segmentos navegables, extraer entidades históricas,
clasificar subtemas con BETO y conservar las correcciones del docente. La unidad
principal es el segmento con su página o intervalo temporal verificable.

## Despliegue público

```text
Docente
  │
  ▼
React 19 + Vite (Vercel)
  │ REST/JSON + JWT
  ▼
NestJS 10 (Render)
  ├── PostgreSQL + pgvector (Neon)
  ├── PDF privados (Supabase Storage, API S3)
  └── FastAPI ML protegido (Modal)
        ├── BETO / embeddings / NER
        ├── subtítulos directos → Supadata → Whisper
        └── pesos BETO v1 (Hugging Face Hub)
```

- **React** presenta proyectos, fuentes, segmentos, revisión, búsqueda,
  colecciones y laboratorio.
- **NestJS** es dueño de usuarios, permisos, metadatos, auditoría, revisiones,
  datasets, modelos y ejecuciones persistentes.
- **Neon** conserva el estado relacional, búsqueda textual y vectores.
- **Supabase Storage** evita depender del disco efímero de Render y permanece privado; los
  archivos se sirven a través de rutas controladas por la API.
- **Modal** ejecuta FastAPI y escala a cero. La comunicación NestJS→ML exige
  token interno y Proxy Token.
- **Hugging Face Hub** almacena los pesos; no ejecuta el servicio web.
- **Supadata** se usa únicamente cuando YouTube bloquea la extracción directa de
  subtítulos desde el centro de datos. Whisper es el último fallback.

## Procesamiento

```text
Fuente
  → validación y deduplicación
  → extracción PDF o transcripción YouTube
  → limpieza y segmentación
  → BETO + años/personas/lugares + embedding
  → ejecución versionada
  → revisión y corrección docente
  → búsqueda y publicación controlada
```

El reprocesamiento crea una nueva ejecución. La extracción anterior permanece
activa hasta que la nueva termina correctamente; las revisiones no se eliminan.
En producción, la cola se persiste en PostgreSQL y se recupera tras reinicios. En
Docker local puede utilizarse Redis/BullMQ.

## Stack efectivo

| Capa | Tecnologías |
|---|---|
| Web | React 19, TypeScript, Vite 6, TanStack Query, React Router, PDF.js, Recharts |
| API | NestJS 10, TypeORM, PostgreSQL, JWT, Swagger, AWS SDK S3 |
| ML | Python 3.11, FastAPI, PyTorch, Transformers, BETO, sentence-transformers, NER, faster-whisper |
| Datos | Neon PostgreSQL, `pgvector`, búsqueda de texto completo |
| Producción | Vercel, Render, Neon, Supabase Storage, Modal, Hugging Face Hub, Supadata |
| Desarrollo | Docker Compose, PostgreSQL, Redis/BullMQ, almacenamiento local |

## Datos y modelo

- Snapshot reproducible: 814 segmentos revisados de 10 fuentes.
- Corte inicial procesado: 11 fuentes y 1,577 segmentos.
- Split agrupado por fuente: 596 train, 81 validation y 137 test.
- BETO v1: F1 macro 0.425.
- TF-IDF + regresión logística: F1 macro 0.353.
- Cohen's Kappa: 0.651, con revisión asistida por IA.

BETO permanece como modelo experimental: su predicción es una sugerencia
corregible y no una autoridad histórica.

## Seguridad y límites de la demo

- CORS restringido a la aplicación Vercel.
- Cuenta pública con rol colaborador.
- Cinco fallos de login por minuto y cliente.
- Tres fuentes nuevas por cuenta compartida.
- PDF de 10 MB en producción y 50 MB/500 páginas en local.
- Bucket privado; publicación del archivo y de los segmentos son estados
  independientes.
- Solo segmentos revisados aparecen en la búsqueda pública.

El esquema base está en
[`ddl.sql`](../apps/api/claude_workspace/architecture/ddl.sql) y las ampliaciones
idempotentes en
[`evolution_historia_viva.sql`](../apps/api/claude_workspace/architecture/evolution_historia_viva.sql).
