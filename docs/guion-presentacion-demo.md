# Guion de presentación — diapositivas + demo final

Estructura pensada para el vídeo del TFM: primero se explican las **13 diapositivas**
(≈5 min) y al final se hace la **demostración en vivo** de la aplicación (≈3–4 min).
Duración total objetivo: **8–9 minutos**.

## Antes de grabar

- Navegador limpio a 1920×1080, zoom 100%. Cierra pestañas y notificaciones.
- Inicia sesión antes de grabar (`docente` / `tfm2026`) y deja **una fuente ya
  procesada** abierta en otra pestaña para no esperar en vivo.
- Ten a mano un PDF pequeño y un vídeo de YouTube con subtítulos.
- Abre el `.pptx` a pantalla completa y ensaya el paso de diapositiva.
- Graba tú misma la voz; la autora debe conducir la presentación.

---

## Parte 1 — Diapositivas (≈0:00–5:00)

### Diapositiva 1 · Portada (0:00–0:25)
> «Hola, soy Jaqueline Ramos. Presento **Historia Viva Perú**, un asistente que
> convierte videos de YouTube y documentos PDF en evidencia histórica navegable
> sobre la Independencia y la formación republicana del Perú, entre 1780 y 1842.
> La idea en una línea: **de la fuente al fragmento verificable**.»

### Diapositiva 2 · Problema (0:25–0:55)
> «La evidencia existe, pero encontrarla cuesta demasiado. Un docente puede tardar
> **30 a 60 minutos** recorriendo un video o un libro para localizar una sola idea,
> comprobarla y luego citarla con su minuto o página exacta.»

### Diapositiva 3 · Usuario (0:55–1:20)
> «El producto está diseñado alrededor del trabajo docente: **añadir** una fuente,
> **comprender** su tema y entidades, **verificar** en la página o el minuto, y
> **corregir** con criterio experto. La complejidad técnica queda oculta.»

### Diapositiva 4 · Producto (1:20–1:55)
> «El núcleo es simple, trazable y corregible. Cada fuente se **segmenta** por
> página o minuto, se **enriquece** con años, personas y lugares, se **clasifica**
> con BETO mostrando su confianza, y queda abierta a **corrección** docente. Lo
> importante: nunca se pierde la procedencia; cada predicción conserva su
> localizador original.»

### Diapositiva 5 · Arquitectura (1:55–2:30)
> «Separar responsabilidades hace viable una demo gratuita. El **frontend en React
> se sirve en Vercel**; la **API NestJS en Render** orquesta todo; los datos con
> **PostgreSQL y pgvector viven en Neon**; los PDF se guardan en **Supabase Storage**;
> y el servicio de machine learning en **FastAPI se ejecuta en Modal**, mientras
> **Hugging Face Hub aloja los pesos del modelo** BETO para poder restaurarlo.»

*(Corrección clave: Modal ejecuta el ML; Hugging Face solo aloja el modelo.)*

### Diapositiva 6 · Stack tecnológico (2:30–3:10)
> «Este es el stack completo, de extremo a extremo. En el **frontend**: React 19,
> TypeScript, Vite, TanStack Query y Tailwind. En la **API**: NestJS, TypeORM, JWT,
> cola recuperable persistida en PostgreSQL y almacenamiento vía S3. En **datos**:
> PostgreSQL con pgvector en Neon y archivos en Supabase Storage. En **ML**: FastAPI,
> Transformers, BETO, embeddings con Sentence-Transformers, NER y scikit-learn,
> desplegado en Modal. La **transcripción** usa subtítulos de YouTube, Supadata como
> respaldo y Whisper para el audio. El **modelo** se publica en Hugging Face Hub y se
> entrena en Colab. Producto y API en TypeScript, ML en Python, todo en planes
> gratuitos.»

### Diapositiva 7 · Datos (3:10–3:40)
> «El corpus es un dataset *gold* con **división por fuente**: 10 fuentes,
> 814 segmentos revisados —670 de PDF y 144 de YouTube—, con un mínimo de 100 ejemplos por
> clase. Lo esencial: una fuente completa pertenece solo a *train*, *validation* o
> *test*, de modo que hay **cero fuentes compartidas** entre entrenamiento y prueba
> y no existe fuga de datos.»

### Diapositiva 8 · Experimento (3:40–4:05)
> «Sobre ese mismo *snapshot* comparé un baseline de TF-IDF con regresión logística,
> que da **0,353** de F1 macro, contra **BETO v1**, que alcanza **0,425**. BETO
> mejora el baseline en algo más de siete centésimas, pero queda **por debajo del
> umbral de recomendación de 0,70**.»

### Diapositiva 9 · Resultados (4:05–4:30)
> «Por eso la honestidad metodológica es parte del producto: BETO se presenta como
> **modelo experimental**, no robusto ni recomendado. Supera al baseline, sí, pero
> no llega a F1 0,70 ni a Kappa 0,70 —quedó en 0,651— y **no participó un historiador
> independiente**. El modelo ayuda a priorizar la revisión; no sustituye el juicio
> docente.»

### Diapositiva 10 · Demostración (4:30–4:45)
> «Todo esto se ve junto en la interfaz: subtema, confianza, entidades y localizador
> en una misma unidad revisable. **Lo enseñaré en vivo al final** de la presentación.»

*(Es el anticipo de la demo; no cambies de pantalla todavía.)*

### Diapositiva 11 · Publicación (4:45–5:05)
> «El despliegue es gratuito pero con diseño operativo explícito: **CORS restringido
> al dominio de Vercel**, login limitado a 5 intentos por minuto, cuota de 3 fuentes
> nuevas y PDF de hasta 10 MB en la cuenta compartida. Los secretos y los archivos
> tienen estrategia, y nada se guarda en discos efímeros.»

### Diapositiva 12 · Limitaciones (5:05–5:25)
> «Y lo que el TFM todavía no demuestra: validación sin historiador independiente,
> modelo aún experimental, alcance limitado al español y al periodo 1780–1842 sin
> OCR, y una operación sujeta a *cold starts* y cuotas gratuitas. Los presento como
> **condiciones de validez**, no como notas al pie.»

### Diapositiva 13 · Conclusión (5:25–5:45)
> «La conclusión es clara: el aporte **no es un modelo perfecto, sino un flujo
> docente verificable** —encontrar evidencia, explicar subtemas, citar la fuente y
> aprender de las correcciones—. El siguiente paso es ampliar el corpus, validar con
> especialistas y evaluar BETO v2 con docentes. **Y ahora, la demostración en vivo.**»

---

## Parte 2 — Demostración en vivo (≈5:45–9:00)

> Cambia del `.pptx` al navegador con la aplicación ya abierta y con sesión iniciada.

### 1. Login y proyecto (5:45–6:05)
- Muestra brevemente la pantalla de acceso ya autenticada.
> «Entro con la cuenta de demostración `docente`. Es una cuenta **colaboradora**, no
> administradora. Selecciono el proyecto y accedo al espacio de trabajo.»

### 2. Añadir una fuente (6:05–6:40)
- Abre **Fuentes**, pega una URL de YouTube (o sube el PDF), marca la declaración
  académica y pulsa **Añadir y procesar**.
> «Añado una fuente: puede ser un YouTube de hasta dos horas o un PDF con texto. La
> app toma los **subtítulos** directos; si YouTube bloquea el servidor usa
> **Supadata**, y como último recurso transcribe el audio con **Whisper**. Para no
> esperar en vivo, paso a una fuente que ya está procesada.»

### 3. Segmentos enriquecidos (6:40–7:20)
- Abre una fuente ya lista y muestra una tarjeta de segmento.
> «Cada segmento trae el **texto**, un **subtítulo temático** sugerido por BETO con
> su **confianza**, el **minuto o la página**, y las entidades: **años, personajes y
> lugares**. Si abro el localizador, salta al **segundo exacto** del video —aquí está
> la trazabilidad de la que hablé.»

### 4. Corrección docente (7:20–7:55)
- Ve a **Revisión**, filtra por baja confianza, corrige una etiqueta y confirma otra.
> «En Revisión filtro los segmentos de baja confianza. Puedo **confirmar**,
> **corregir**, marcar **ambiguo** o **excluir**. Esta corrección entra como
> *feedback* para un snapshot posterior: **nunca reentrena el modelo activo al
> instante**.»

### 5. Búsqueda verificable y abstención (7:55–8:40)
- En **Buscar**, lanza una consulta válida y abre una evidencia con su cita.
> «En Buscar consulto, por ejemplo, la expedición libertadora de San Martín, y abro
> la evidencia en su minuto original.»
- Luego escribe una pregunta fuera de alcance.
> «Y ahora pregunto algo fuera del corpus: *¿qué relación tuvo el Apolo 11 con la
> Independencia peruana?* El sistema **se abstiene** porque no hay respaldo
> suficiente. Prefiere no responder antes que inventar: eso es clave en un uso
> docente.»

### 6. Cierre (8:40–9:00)
> «En resumen: de un video o un PDF llegamos a fragmentos temáticos, localizados y
> corregibles, con búsqueda que cita la fuente y se abstiene cuando no sabe. Gracias.»

---

## Después de grabar

1. Sube el vídeo a YouTube (no listado) o a Drive público.
2. Verifica el enlace en una ventana **sin sesión iniciada**.
3. Sustituye `PENDIENTE_URL_VIDEO` en el README por la URL final.
