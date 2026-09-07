# Plan de trabajo: Unidad I y Unidad II

Este documento separa implementación, ejecución local y evidencia en producción.
Una configuración escrita no equivale a un pipeline ejecutado en GitHub.

## Orden de trabajo

| Bloque | Resultado | Estado |
|---|---|---|
| Diagnóstico | Compilar web/API, ejecutar suites y revisar dataset | API 37 pruebas, ML 55 pruebas y web verificados localmente |
| Experimentos | Comparar hiperparámetros usando validación; test solo del ganador | Tres configuraciones TF-IDF y tres BETO ejecutadas en este equipo |
| Comparación tras revisión | Medir el efecto conjunto del enriquecimiento y las correcciones | TF-IDF local: F1 macro validación 0.29004 en ambas versiones; test 0.36300 → 0.36007. Sin mejora global ni cambio en producción |
| Comparación con Huerta | Medir los cuatro pasajes añadidos con configuración fija | TF-IDF local C=4: F1 macro validación 0.29004 → 0.28968; crisis e ideas sigue en 0. Sin mejora; no se calcularon métricas nuevas de test ni se cambió producción |
| Comparación de Villanueva | Medir la sustitución con la misma configuración | TF-IDF local C=4: F1 macro validación 0.28968 → 0.28987; mismos 25/81 aciertos, ideas sigue en 0. Sin mejora útil demostrada ni cambios en producción |
| Generalización entre fuentes | Evaluar cada fuente de train sin usarla para entrenar | Nueve rondas locales: F1 macro agregado 0.32372, 208/598 aciertos; ideas 5/60. Diagnóstico interno, no mejora frente a validación ni prueba final |
| Diagnóstico de cobertura | Orientar el siguiente cambio de datos | Concentración por fuente, rasgos de transcripción y fragmentos incompletos identificados. Muestra de 21 filas de train revisada; prioridad: cuatro filas de Villanueva. Sin modificar etiquetas |
| Límites de Villanueva | Recuperar argumentos cortados entre páginas | Seis unidades delimitadas y cotejadas; dos quedan como contexto. Continuaciones ya presentes en filas 10/637 identificadas. Propuesta local, sin aplicar |
| Reparación de Villanueva | Preparar un reemplazo sin duplicar continuaciones | Cuatro candidatos revisados, cuatro unidades de contexto y seis originales archivados; V02 ambiguo. Extracción local verificada, dataset sin modificar |
| Copia experimental Villanueva | Aplicar únicamente la sustitución revisada | Seis filas sustituidas por cuatro: 598 train, 81 validación, 137 test. Otras 812 filas idénticas; originales y contexto archivados. Sin entrenamiento ni despliegue |
| Fuente para crisis e ideas | Localizar contenido pertinente y reutilizable | HUE01 de Huerta Vera (2020), revisado por ambos agentes, incorporado a copia experimental local: 597 train, 81 validación y 137 test. Evaluación intacta; sin entrenamiento nuevo |
| Lote adicional de Huerta | Revisar propaganda, lecturas políticas y prensa | HUE02/03/04 incorporados a copia experimental: 600 train, 81 validación y 137 test. Una fuente común y dependencia HUE03/HUE04 conservadas; sin entrenamiento nuevo |
| Revisión histórica inicial | Auditar 20 fragmentos de train antes de enriquecer el corpus | Segunda revisión: 11 aprobar, 2 corregir, 6 ambiguos y 1 excluir hasta resegmentar. R04/R16 corregidos solo en copia experimental; referencia y producción intactas |
| Reparación de R05 | Recuperar prosa separada por notas y salto de página | Sustitución local verificada: train55/57/58 reemplazadas por un fragmento de 203 palabras en una nueva copia experimental. Originales y contexto archivados; referencia intacta |
| Fuentes para enriquecimiento | Evaluar contenido, procedencia, reutilización y solapamientos | Tres candidatas examinadas; dos fragmentos AGN incorporados solo a copia experimental local. BNP pendiente de OCR/metadatos y Constitución pendiente de cotejo |
| Piloto AGN | Preparar hasta tres fragmentos con procedencia y etiquetas propuestas | Tres etiquetas coincidentes tras segunda revisión asistida por IA. AGN01/02 candidatos a entrenamiento futuro; AGN03 solo contexto. Snapshot y producción intactos |
| Copia experimental AGN | Incorporar los dos candidatos y comprobar el mantenimiento | Export local verificado; referencia y evaluación intactas. Mantenimiento omitió entrenar: dos cambios frente al mínimo de 20. Sin métricas nuevas ni despliegue |
| Informe Unidad I | Dataset, características, parámetros, resultados, despliegue y límites | Borrador en informe-unidad-1.md |
| Demo Unidad I | Dos pruebas funcionales completas y explicación en inglés | PDF cargado, predicho tras reintento y revisión persistida vía API. Primera clasificación fallida y recorrido visual pendientes |
| Mantenimiento | Validar snapshot, entrenar, evaluar y archivar candidato | TF-IDF ejecutado en GitHub; métricas y candidato archivados. Correcciones automáticas pendientes |
| Integración continua | Tests, builds y comprobación agregada Quality gate | Ejecución en GitHub correcta para `fca473d`, con acciones v6 y API en Node 22 |
| Despliegue | Esperar CI, verificar versión y recuperar ante fallos | Modal con SHA y predicción verificados para `fca473d`; seis pruebas de Production smoke aprobadas. Render `328ab3c` confirmado por la autora. Controles API/web y recuperación pendientes |
| Entrega Unidad II | Tres casos ejecutados, con logs y resultados | Controles locales; demostración remota pendiente |

## Organización de los cambios en Git

Las consultas de Git pueden realizarlas el asistente o la autora. Las ramas, el staging, los commits, los merges y el push los gestiona exclusivamente la autora. Cada bloque se revisa y verifica antes de registrarlo; se espera su confirmación para pasar al siguiente. Publicar o desplegar requiere su autorización.

| Bloque | Commit local verificado | Estado |
|---|---|---|
| Salud de la API y pruebas | `ca2da38` | Publicado; ruta accesible en Render |
| Experimentos y preparación del reentrenamiento | `3548851` | Registrado; pruebas locales correctas |
| Scripts de verificación | `2483a4f` | Registrado; pruebas locales correctas |
| Automatización y configuración de Render | `62073ac` | Publicado; CI y mantenimiento TF-IDF ejecutados correctamente |
| Evidencias e informes | `847b141` | Publicado |
| Exclusiones del material local | `3974f4a` | Publicado; presentación conservada localmente |
| Arranque de BETO antes de aceptar peticiones | `24f03be` | Publicado; Modal v7 desplegado manualmente y predicción verificada |
| Errores de almacenamiento PDF | `0bc365a` | Registrado; pruebas y compilación correctas, despliegue API pendiente |

Las modificaciones personales de `.gitignore` se revisan por separado.

## Revisión histórica de 20 fragmentos — registrada en `95e9dd1`

La propuesta está en [history-review-v1.json](../artifacts/reviews/history-review-v1.json).
Cada registro conserva índice (base cero), fuente, hash del texto y etiqueta original,
además de decisión, justificación temática, límites del contraste histórico y contexto consultado.
El snapshot no conserva identificador de segmento, página, minuto ni predicción individual:
esta revisión evalúa **etiquetas del dataset**, no el acierto actual de BETO.
Todas las decisiones conservan `applied: false`. La autora delegó después el juicio
histórico en una segunda revisión asistida por IA; el nuevo dictamen se describe
en el bloque actual, conservando este primer registro intacto.

Se seleccionaron tres ejemplos por categoría histórica y dos de `no_relevante`,
solo de train, mediante orden SHA-256 con semilla 42. Se ocultaron las etiquetas
en la primera lectura, pero la selección usó esas etiquetas y existía contexto previo;
no es una revisión humana independiente ni un estudio ciego. La muestra contiene
cuatro de las siete fuentes de train, con 12/20 ejemplos de Basadre: no permite
estimar la tasa de errores del corpus. Las decisiones son reproducibles como registro;
el criterio del revisor no se convierte por ello en una verdad automática.

Resultado de la propuesta: **12 aprobar, 2 corregir, 5 ambiguos y 1 excluir**.
Las correcciones propuestas son R04 (dinámica regional, en lugar de crisis e ideas)
y R16 (condiciones diplomáticas, en lugar de campañas militares). R05 mezcla unas
líneas sustantivas con bibliografía: excluir significa apartar esa extracción de un
futuro entrenamiento hasta resegmentarla, conservando intacto el original.
R09 requiere recuperar la página: otros fragmentos de la misma fuente apuntan a
un reglamento de 1825, lo que podría invalidar su etiqueta de antecedentes coloniales;
sin continuidad física confirmada se deja ambiguo. No se certifica la exactitud de
todas las afirmaciones históricas por aprobar una etiqueta temática.

Se consultaron la guía de etiquetado, los informes existentes, fragmentos de train,
el inventario local y pasajes de dos PDF ya descargados. Las fichas editoriales de
[O'Phelan (1985)](https://revistas.pucp.edu.pe/index.php/historica/article/view/8222)
y [Fonseca (2010)](https://revistas.pucp.edu.pe/index.php/historica/article/view/95)
confirman autoría y muestran CC BY 4.0. No se encontró el PDF de Basadre ni se
escuchó el video; los casos que necesitan ese contexto lo indican. No se incorporan
textos originales ni PDF al commit; las copias legibles quedan en `outputs/`.

Hallazgos que orientan el siguiente experimento:

- El candidato BETO seleccionado obtuvo F1 de validación **0 en crisis e ideas**
  (15 casos; nueve confundidos con organización republicana). Train tiene 59 casos
  de esa clase. Es una señal para revisar fronteras temáticas y diversidad, no prueba
  de que todas esas etiquetas estén mal. No se adjudicaron etiquetas de validación en este bloque.
- Validación contiene una sola fuente y apenas cuatro casos de campañas y cuatro
  de liderazgos. Harán falta fuentes independientes para una evaluación futura;
  no se cambia la partición congelada ni se utiliza el test para elegir correcciones.
- El BETO de estos experimentos obtuvo F1 test 0.31066 frente a 0.36300 del TF-IDF
  seleccionado. Esos resultados ya existentes no son métricas de esta revisión.
- Antes de enriquecer: recuperar páginas/minutos y procedencia, reparar extracción
  y resolver criterios entre programas políticos, participación regional y organización estatal.

## Selección de fuentes gratuitas — registrada en `42ee37d`

El registro auditable está en [source-candidates-v1.json](../artifacts/reviews/source-candidates-v1.json).
Contiene procedencia, fecha cuando se conoce, localizadores, decisiones, límites de
reutilización y comprobaciones de solapamiento. Las tres candidatas se mantienen
**sin incorporar en ese bloque**; la incorporación experimental posterior de AGN
se describe más abajo. BNP y Constitución siguen pendientes.

| Candidata | Carencia que podría cubrir | Resultado de la revisión |
|---|---|---|
| [La Abeja Republicana, BNP](https://repositoriodigital.bnp.gob.pe/bnp/recursos/2/html/la-abeja-republicana/56/) | Prensa e ideas políticas | Página 56 del visor con argumentación antimonárquica; OCR defectuoso. Faltan fecha/número, autoría y condiciones de reutilización de la edición. Posponer extracción |
| [Constitución de 1823, Congreso Constituyente / Congreso de la República](https://www3.congreso.gob.pe/Docs/sites/webs/quipu/constitu/1823.htm) | Organización estatal y ciudadanía | Artículos 17, 22–23 y 27–29 localizados en HTML. Hay una anomalía de numeración entre 32 y 34 y una cita del artículo 11 ya en train. Cotejar y resolver solapamientos; derechos de la edición sin verificar |
| [Juan José Brito Ramos, Josefa Montes, la última esclava del Congo (2017), Revista del AGN 32(1), 15–45](https://revista.agn.gob.pe/ojs/index.php/ragn/article/view/5) | Contexto colonial y actuación de cofradías afrodescendientes | Licencia CC BY 4.0 comprobada; PDF local de 1 128 046 bytes. Pasajes candidatos en pp. 21, 35 y comienzo de 36, con fechas 1805, 1834 y 1836. Propuesto para un piloto pequeño |

Se contrastó una afirmación de la p. 17 del artículo del AGN: sitúa la abolición
británica de la esclavitud en 1808. La [cronología del Parlamento británico](https://www.parliament.uk/about/living-heritage/transformingsociety/tradeindustry/slavetrade/key-dates/)
distingue la ley contra el tráfico de 1807 de la ley de abolición de 1833. Ese pasaje
queda apartado del piloto; no se corrige silenciosamente el documento. En la p. 36
debe detenerse la selección antes del testamento de 1875, fuera del alcance.
La clasificación temática propuesta no certifica todas las afirmaciones de la fuente.

La búsqueda preliminar de cinco frases cortas en los **596 ejemplos de train**
encontró una cita constitucional en el índice 9, fuente `9154f7f7-86c9-4bad-bcba-47eaf54b93e1`.
La ausencia de las otras frases no demuestra novedad: falta comparar los fragmentos
concretos y las citas compartidas. De validación/test solo se consultaron las
identidades y títulos de fuentes; no se extrajeron ejemplos para entrenar.

El único PDF descargado quedó en `outputs/source-candidates-v1/josefa-montes.pdf`,
excluido de Git, con su hash registrado. No se invocó Modal, entrenamiento remoto ni
escrituras en producción. El intento de cotejar el PDF constitucional desde la
herramienta web devolvió 403; solo se verificó la transcripción HTML. Estas fuentes
no resuelven todavía la carencia de ejemplos listos de crisis e ideas: no se debe
forzar esa etiqueta a los pasajes sociales del AGN.

Comprobación local: esquema y localizadores del registro, hash/tamaño del PDF,
reproducción de las cinco búsquedas, dataset intacto y exclusión del PDF por Git.
La selección de fuentes quedó registrada en `42ee37d`. El piloto posterior se
describe a continuación. El segundo dictamen de las 20 etiquetas se registra
por separado más abajo; registrar un commit no aplica las propuestas al dataset.

## Tres candidatos locales del AGN — registrados en `749eb9c`

El [manifiesto del piloto](../artifacts/reviews/agn-pilot-v1.json) registra autoría,
licencia, páginas, límites exactos, hashes, ajustes de extracción, justificaciones
y resultados de similitud. Los textos completos y su revisión legible están en
`outputs/agn-pilot-v1/`, excluido de Git. No son todavía ejemplos gold ni resultados
de predicción: se propusieron etiquetas mediante revisión asistida por IA.

| Candidato | Página impresa / PDF | Palabras | Etiqueta propuesta |
|---|---|---|---|
| AGN01: abastecimiento y compraventa de 1805 | 21 / 7 | 138 | Contexto colonial y antecedentes |
| AGN02: representación de una cofradía en compra de 1834 | 35 / 21 | 210 | Participación social y regional |
| AGN03: pago del saldo de 1836 | 36 / 22 | 126 | Participación social y regional |

Se unieron saltos y palabras partidas al final de línea; se retiraron dos llamadas
de nota y una marca de folio, conservando grafía histórica y cantidades. La fecha
de AGN02 está en el contexto de la página y no se añadió al texto. El cotejo fue
contra la capa de texto del PDF; no se verificaron manuscritos ni imágenes de las páginas.
AGN02 y AGN03 son partes relacionadas de una operación. Los tres candidatos
pertenecen a **una sola fuente**, que deberá conservarse unida en una futura partición.

Se compararon mecánicamente los candidatos con los 814 registros del snapshot:
sin duplicados exactos ni coincidencias que superen los umbrales de secuencias de
cinco palabras (Jaccard ≥ 0.25 o coincidencia respecto al conjunto menor ≥ 0.8).
Solo se guardan indicadores de validación/test, sin exportar ni adjudicar sus textos.
Este control no descarta paráfrasis o dependencia documental; la relación entre
AGN02 y AGN03 se conserva aunque su similitud léxica sea baja.

Reproducción local, usando el PDF ya descargado y una salida nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/prepare_agn_pilot.py --output outputs/agn-pilot-v1/reproduccion.json
```

El script requiere `pypdf` (5.9.0 en el entorno usado), valida hashes de entrada,
límites únicos y longitud, y rechaza sobrescrituras o salidas fuera de `outputs/`.
No descarga archivos, entrena ni conecta con producción. La revisión legible está
en `outputs/agn-pilot-v1/revision-legible.md`.

Verificación local: extracción repetida idéntica, manifiesto coincidente con los
textos, longitudes válidas, 814 comparaciones por candidato y detección de un
duplicado conocido usado como control. Pasaron los rechazos de PDF incorrecto,
límites inexistentes, texto demasiado corto, sobrescritura y salida fuera de
`outputs/`. El snapshot quedó intacto byte a byte; `git diff --check` pasó.

## Segunda revisión mediante otro agente — registrada en `a0cd0c3`

La autora indicó que no es especialista en historia y solicitó explícitamente otro
agente para verificar las propuestas. El juicio temático se delegó a ese revisor;
no se le exige a la autora certificar hechos históricos. El control de Git y las
autorizaciones de publicación/producción siguen a su cargo.

El [registro de segunda revisión](../artifacts/reviews/agn-pilot-v1-peer-review.json)
conserva agente, hashes de entradas, primera clasificación previa a la comparación,
contexto consultado y decisiones. El agente recibió los textos sin las etiquetas
en su primera lectura y comunicó sus etiquetas antes de consultar el manifiesto.
Eso reduce la influencia de la propuesta inicial, pero no constituye validación
humana ni independencia del sistema: ambos revisores pueden compartir sesgos.

| Candidato | Dictamen temático del segundo agente | Selección recomendada |
|---|---|---|
| AGN01 | Coincide: contexto colonial | Candidato para entrenamiento futuro, preservando las reservas de la fuente |
| AGN02 | Coincide: participación social | Candidato para entrenamiento futuro, conservando contexto y fecha documental |
| AGN03 | Coincide: participación social | Solo soporte contextual de AGN02; no añadir como fila separada |

AGN03 no se reclasifica como `no_relevante`: su etiqueta es defendible, pero el
recibo repite actores y operación de AGN02. La selección de ejemplos es distinta
de su clasificación. Se adopta esta recomendación para el siguiente bloque sin
alterar el primer manifiesto ni el snapshot. La referencia complementaria de
[Lévano Medina (2022)](https://revistas.pucp.edu.pe/index.php/revistaira/article/view/26040)
respalda el tratamiento social de las cofradías; no verifica esta compraventa y su
periodo de estudio no se incorpora al corpus de 1780–1842.

Los hashes y las tres etiquetas fueron contrastados con las entradas; la selección
es de dos candidatos y un apoyo contextual. Se verificó que el dataset y el primer
manifiesto permanecen intactos. No se calcula Kappa, accuracy o F1 con tres casos.
Esta decisión es un consenso asistido por IA, no gold validado por historiadores.

El segundo dictamen AGN quedó registrado en `a0cd0c3`. En ese bloque aún faltaba
la segunda revisión de las 20 decisiones iniciales, abordada posteriormente abajo.
No se entrenó ni se escribieron revisiones en producción durante ese bloque.

## Copia experimental AGN y mantenimiento local — registrada en `22ad8f6`

[build_agn_snapshot.py](../scripts/build_agn_snapshot.py) conserva las 814 filas de
la referencia y añade exclusivamente AGN01/02 a entrenamiento, con una identidad
de fuente común derivada del DOI. Comprueba los hashes de las entradas revisadas,
el consenso y los textos. Guarda autoría, licencia, páginas y origen de las
anotaciones dentro del export. AGN03 sigue como contexto; el dataset congelado
no se modifica. Las anotaciones nuevas son asistidas por IA, no gold humano.

La [evidencia compacta](../artifacts/reviews/agn-snapshot-v1.json) registra hashes,
controles y resultados. Los archivos con textos completos quedan en
`outputs/agn-snapshot-v1/`, excluidos de Git.

| Archivo | Entrenamiento | Validación | Test | Total |
|---|---|---|---|---|
| Referencia intacta | 596 | 81 | 137 | 814 |
| Export experimental | 598 | 81 | 137 | 816 |
| Snapshot preparado por mantenimiento | 597 | 81 | 137 | 815 |

La diferencia de una fila procede de un duplicado exacto ya existente en train
(índices 718 y 746, base cero, fuente Basadre). El preparador de mantenimiento
existente lo unifica. Se verificó que conserva todos los ejemplos originales
distintos y los 218 registros de evaluación en el mismo orden. No hay fuentes
compartidas entre particiones.

El mantenimiento local detectó **dos incorporaciones, cero eliminaciones de
ejemplos únicos y cero cambios de etiqueta**. Con su mínimo habitual de 20 cambios,
respondió `skipped / insufficient_changes`: no entrenó un modelo experimental.
No hay nueva F1 ni llamadas a Modal o a producción en este bloque.

Reproducción con las entradas locales del piloto ya disponibles y una carpeta nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/build_agn_snapshot.py --output outputs/agn-snapshot-reproduccion
$env:PYTHONPATH = 'apps/ml'
outputs/venv-ml/Scripts/python.exe -m app.ml.maintenance --reference artifacts/datasets/gold-v1-source-aware.json --reviewed outputs/agn-snapshot-reproduccion/reviewed-export.json --config configs/experiments/tfidf.json --output outputs/agn-snapshot-reproduccion/maintenance
```

El export requiere el PDF y `candidates-verified.json` locales cuyos hashes figuran
en el segundo dictamen. Conserva `reviewed-export.json` y `build-report.json` junto
al resultado: el preparador existente enlaza el export por hash, pero no copia
su registro de procedencia al snapshot derivado.

Verificación: export repetido idéntico, referencia intacta, evaluación preservada,
duplicado identificado y rechazos ante selección incorrecta, falta de consenso,
hash alterado, sobrescritura y salida fuera de `outputs/`. Pasaron las tres pruebas
existentes de mantenimiento. La comprobación inicial del número de filas se ajustó
tras identificar el duplicado; no se cambió la lógica de mantenimiento.

La copia experimental quedó registrada en `22ad8f6`; continúa intacta durante la
revisión posterior. Falta material adecuado de crisis e ideas antes de un
experimento que pueda evaluar mejoras.

## Segunda revisión de los 20 fragmentos iniciales — registrada en `e2c3e74`

El [nuevo dictamen](../artifacts/reviews/history-review-v1-peer-review.json)
conserva la primera etiqueta del segundo agente, comparación con el primer
revisor, decisión final, motivos, contexto y límites por caso. El agente comunicó
su primera lectura antes de consultar etiquetas y razones del primer dictamen.
Después hubo discusión entre agentes: no se presenta como validación humana
independiente ni se calcula Kappa o una nueva F1.

| Decisión sobre la etiqueta original | Primera revisión | Segunda revisión |
|---|---|---|
| Aprobar | 12 | 11 |
| Corregir | 2 | 2 |
| Ambiguo | 5 | 6 |
| Excluir esta extracción hasta resegmentar | 1 | 1 |

Las correcciones propuestas coinciden: R04 pasa de crisis e ideas a participación
social y regional; R16, de campañas militares a liderazgo y diplomacia. R05 mezcla
notas con un argumento cortado: requiere recuperar el párrafo de Fonseca, sin
borrar el original. R07 conserva `no_relevante`: una presentación contemporánea
puede ser un ejemplo negativo válido para entrenamiento.

R06 mantiene un desacuerdo: el primer revisor aprobó militar; el segundo observa
un peso comparable de correspondencia política. Se adopta **ambiguo** por ahora.
R18 pasó de militar en la primera lectura del segundo agente a ambiguo después
de discutir el criterio, sin nueva evidencia documental. Se conserva esa secuencia
y no se fuerza una corrección. También siguen ambiguos R03, R09, R10 y R13.

El segundo agente leyó páginas completas de los PDF de O’Phelan (PDF 6, 24, 34)
y Fonseca (PDF 4, 5, 11). Para Basadre solo hubo fragmentos de train; el original
y la edición no están recuperados. Para el video no se cotejó audio ni tiempos.
La vecindad de índices no demuestra continuidad entre páginas. Aprobar el tema
no certifica los hechos o interpretaciones históricas de cada autor.

Verificación local: selección reproducible, 20 índices y hashes coincidentes,
todos de train, recuentos y etiquetas coherentes; dataset, primer manifiesto y
export AGN intactos. No se consultaron textos de evaluación para adjudicar casos,
no se entrenó ni se escribió en producción. La vista legible con textos se guarda
en `outputs/history-review-v1/segunda-revision-legible.md`, excluida de Git.

El dictamen quedó registrado en `e2c3e74`. Las correcciones resueltas solo se
aplicarán en otro bloque experimental; los seis casos ambiguos requieren contexto
adicional. La recuperación de R05 se describe a continuación.

## Recuperación del texto de R05 — registrada en `0cb6cbd`

[prepare_fonseca_repair.py](../scripts/prepare_fonseca_repair.py) recupera prosa de
las páginas impresas 108–109 (PDF4–5) de Fonseca. Une la frase interrumpida entre
páginas, excluye notas y encabezado, y retira las llamadas bibliográficas 5–8.
Conserva las grafías y atribuciones; CDIP se mantiene como sigla. Las entradas,
límites de extracción y cambios quedan fijados para reproducir el resultado.

El candidato `FON-R05-v1` tiene **203 palabras**. Comienza con los testimonios sobre
guerrilleros y completa la interpretación del testimonio de Riva Agüero. Termina
en una oración completa antes de anunciar la tabla siguiente. El segundo agente
considera coherente la selección y propone `participacion_social_regional`.
La revisión es asistida por IA y discutida entre agentes; no certifica como hechos
las acusaciones y caracterizaciones que la fuente analiza.

La [evidencia de reparación](../artifacts/reviews/fonseca-repair-v1.json) contiene
procedencia, hashes, dictamen y solapamientos. El texto y su vista legible están
en `outputs/fonseca-repair-v1/`, excluidos de Git.

**No es una fuente ni un ejemplo independiente nuevo.** La comparación léxica
marca train55 (Jaccard 0.456274). También reutiliza prosa de R05/train57 y
R12/train58, aunque esos tramos no superan el umbral automático. Las tres relaciones
se conservan. El candidato queda `pending_group_replacement`: no añadirlo ni
eliminar automáticamente las tres filas originales, que contienen otros tramos.

Reproducción con los PDF locales ya disponibles y una salida nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/prepare_fonseca_repair.py --output outputs/fonseca-repair-v1/reproduccion.json
```

Verificación local: reproducción idéntica, 203 palabras, frase unida correctamente,
notas excluidas y 814 comparaciones léxicas. Sin coincidencias exactas ni superiores
al umbral con validación/test; solo se consultaron indicadores de esos conjuntos.
Pasaron los controles de límites, hash, ajustes, longitud, sobrescritura y ruta.
El dataset congelado y el export AGN permanecen intactos; no hubo entrenamiento
ni llamadas a servicios remotos.

La recuperación quedó registrada en `0cb6cbd`. El candidato no aumenta el corpus;
la decisión posterior de sustitución se documenta a continuación.

## Sustitución experimental del grupo Fonseca — registrada en `f300747`

El [dictamen de sustitución](../artifacts/reviews/fonseca-replacement-v1.json)
registra una decisión discutida con el segundo agente: reemplazar conjuntamente
train55/57/58 por `FON-R05-v1` en una **copia experimental nueva**, con la misma
fuente, partición de entrenamiento y etiqueta social. Una selección más estrecha
sustituye tres extracciones; se reduce cobertura dentro del entrenamiento y no
se afirma que esta reducción mejore las métricas.

[build_fonseca_snapshot.py](../scripts/build_fonseca_snapshot.py) comprueba hashes,
reproduce el candidato, aplica únicamente esa sustitución y conserva la procedencia
AGN. Produce tres archivos locales en `outputs/fonseca-snapshot-v1/`:

- `reviewed-export.json`: copia experimental, 814 filas (596 train, 81 val, 137 test).
- `replacement-archive.json`: las tres filas originales y las páginas PDF3–5,
  tanto en texto como con disposición espacial; quedan fuera de entrenamiento.
- `build-report.json`: hashes, recuentos y auditoría de particiones.

El archivo de contexto conserva el pasaje de viajeros, la interpretación que
introduce la tabla Pueblo/Elite, la prosa sobre historiografía nacionalista,
notas 3–10 y definición de CDIP. No se convierten en ejemplos negativos ni se
añaden automáticamente como otras filas. La tabla conserva su disposición
extraída del PDF; no hubo cotejo visual renderizado ni verificación de testimonios
originales. Esta revisión sigue siendo asistida por IA.

Verificación local: tres salidas reproducidas de forma idéntica; las **813 filas
ajenas a la sustitución**, incluidos los dos ejemplos AGN, permanecen iguales.
Los 218 registros de evaluación conservan texto, etiquetas y orden. El dataset
congelado y el export AGN anterior siguen intactos. No quedan coincidencias
léxicas superiores al umbral fuera del grupo sustituido; eso no prueba ausencia
de paráfrasis. Se comprobaron también originales y páginas archivadas.

Pasaron siete controles de rechazo: decisión pendiente, hash alterado, índice
repetido, índice negativo, intento de sustituir evaluación, etiqueta incorrecta
y duplicado fuera del grupo. También pasaron las protecciones de sobrescritura
y ruta. No hubo entrenamiento, métricas nuevas ni cambios en producción.

Reproducción con las entradas locales de los bloques previos y una carpeta nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/build_fonseca_snapshot.py --output outputs/fonseca-snapshot-reproduccion
```

La sustitución quedó registrada en `f300747`. Las correcciones consensuadas
R04/R16 se aplican en otra versión experimental, descrita a continuación.

## Aplicación de las correcciones R04 y R16 — registrada en `a996f24`

[apply_reviewed_labels.py](../scripts/apply_reviewed_labels.py) aplica únicamente
correcciones solicitadas por identificador y coincidentes entre ambos dictámenes.
Localiza cada texto por fuente y SHA-256, no por su antigua posición: la sustitución
de Fonseca desplazó R04 del índice 360 al 357 y R16 del 536 al 533 (base cero).
También comprueba la etiqueta original, la unicidad del texto y la pertenencia
a entrenamiento. Rechaza casos ambiguos y correcciones ya aplicadas.

| Caso | Etiqueta anterior | Etiqueta corregida |
|---|---|---|
| R04 | Crisis e ideas emancipadoras | Participación social y regional |
| R16 | Campañas y conflictos militares | Liderazgos, diplomacia y proyectos |

La [evidencia de aplicación](../artifacts/reviews/history-corrections-v1.json)
registra entradas, hashes, motivos y controles. La nueva copia está en
`outputs/history-corrections-v1/reviewed-export.json`; su informe está en
`build-report.json` del mismo directorio. Conserva **814 filas: 596 train,
81 validación y 137 test**. Solo cambian las dos etiquetas: ningún texto cambia,
las otras 812 filas permanecen iguales y se conserva la procedencia de AGN y
Fonseca. Mantener también `outputs/fonseca-snapshot-v1/replacement-archive.json`:
el informe identifica el directorio padre donde permanece ese contexto.

Los primeros dictámenes se conservan como registros históricos sin sobrescribir
sus campos `applied: false`. La aplicación posterior queda en esta evidencia y en
el historial de correcciones de la nueva copia. La referencia congelada, las
versiones anteriores y los seis casos ambiguos permanecen intactos.

Verificación local: reproducción idéntica, exactamente dos etiquetas cambiadas,
evaluación preservada y metadatos anteriores conservados. Pasaron 13 controles
negativos sobre decisiones, consenso, identidad, unicidad, etiqueta previa y
evaluación, además de sobrescritura y salida fuera de `outputs/`.
No hubo entrenamiento, métricas nuevas ni despliegue. Esta aplicación sigue
siendo asistida por IA; no crea validación humana independiente.

Reproducción con las entradas locales previas y una carpeta nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/apply_reviewed_labels.py --base outputs/fonseca-snapshot-v1/reviewed-export.json --review artifacts/reviews/history-review-v1-peer-review.json --ids R04 R16 --output outputs/history-corrections-reproduccion
```

Las correcciones quedaron registradas en `a996f24`. La clase de crisis e ideas
queda con 58 filas de train: sigue pendiente enriquecerla con contenido pertinente,
sin mantener etiquetas incorrectas por su frecuencia.

## Comparación TF-IDF después de la revisión — registrada en `fd0d0ce`

Se ejecutó el entrenador existente dos veces: sobre la referencia congelada y
sobre `outputs/history-corrections-v1/reviewed-export.json`. Ambas versiones
tienen 596 filas de train, 81 de validación y 137 de test; la evaluación es idéntica.
El duplicado preexistente de train permanece en ambas ejecuciones. El cambio de
datos combina dos ejemplos AGN, la sustitución de tres extracciones de Fonseca
por una y las dos correcciones de etiqueta; no se aislaron sus efectos individuales.

La [comparación completa](../artifacts/experiments/history-comparison-v1/comparison.json)
conserva hashes, configuración, entorno, métricas por clase y matrices de confusión.
Se utilizaron los mismos C (0.25, 1 y 4), semilla 42 y versiones de NumPy y
scikit-learn. El equipo tenía 15.34 GB de RAM total y 0.45 GB libres al comprobarlo;
las ejecuciones fueron secuenciales con un hilo configurado. No se midió el pico
real de RAM ni se usaron servicios remotos.

| Dataset | C seleccionado por validación | F1 macro validación | F1 macro test | Aciertos en test |
|---|---|---|---|---|
| Referencia congelada | 4 | 0.29004 | 0.36300 | 57/137 |
| Copia revisada | 4 | 0.29004 | 0.36007 | 57/137 |

**No se observa mejora global.** La variación de F1 macro test es −0.00293
(−0.293 puntos porcentuales); validación y accuracy de test permanecen iguales.
F1 macro promedia el resultado de cada clase, por lo que puede variar aunque el
número total de aciertos coincida. La clase de crisis e ideas conserva F1 de
validación 0 con 15 casos; continúa siendo una carencia que investigar.

Cada ejecución seleccionó por validación antes de evaluar el trial ganador en
test. El ejecutor también ajusta y evalúa un baseline fijo C=1 que no interviene
en la selección: en total se hicieron ocho ajustes y se guardaron seis modelos
de trials. El experimento manual no cambia el mínimo de 20 cambios del
mantenimiento automático.

Verificación: la referencia reprodujo las tres validaciones y las métricas de test
del experimento original. Se comprobaron configuraciones, dependencias, selección,
recuentos y F1/accuracy calculadas desde las matrices de confusión. Los dos datasets
permanecen intactos. Modelos y reportes completos están en
`outputs/history-comparison-v1/reference/` y `outputs/history-comparison-v1/reviewed/`,
excluidos de Git. La ejecución se hizo con el árbol limpio en `a996f24`.

Reproducción con carpetas nuevas:

```powershell
$env:PYTHONPATH = 'apps/ml'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
outputs/venv-ml/Scripts/python.exe -m app.ml.experiments --dataset artifacts/datasets/gold-v1-source-aware.json --config configs/experiments/tfidf.json --output outputs/history-comparison-reproduccion/reference
outputs/venv-ml/Scripts/python.exe -m app.ml.experiments --dataset outputs/history-corrections-v1/reviewed-export.json --config configs/experiments/tfidf.json --output outputs/history-comparison-reproduccion/reviewed
```

La comparación es descriptiva: el test ya se consultó anteriormente y no es una
evaluación externa nueva. No se demostró significación estadística ni mejora de
BETO, que permanece en producción sin cambios. Las correcciones históricamente
justificadas se conservan; el candidato TF-IDF sigue experimental.

La comparación quedó registrada en `fd0d0ce`. La búsqueda posterior de una fuente
complementaria se basa en las carencias de entrenamiento/validación; no se generan
ejemplos copiando el test ni se ajustan etiquetas para mejorar su resultado.

## Fuente complementaria para crisis e ideas — registrada en `e235873`

Se seleccionó para un próximo piloto [Huerta Vera (2020), «Desde el sagrado
púlpito y en exhortaciones privadas»](https://revistas.pucp.edu.pe/index.php/historica/article/view/23275),
publicado en *Histórica*, 44(1), 125–158. La ficha editorial identifica CC BY 4.0.
El PDF público descargado tiene 465 826 bytes y 34 páginas; se conserva en
`outputs/ideas-source-v1/huerta-2020.pdf`, excluido de Git, con hash registrado.

La [ficha de selección](../artifacts/reviews/ideas-source-v1.json) documenta licencia,
autoría, localizadores, alternativas, controles y límites. El segundo agente
propuso la p.145 (PDF21), donde la justificación religiosa de la independencia
domina un pasaje sobre una proclama peruana. La nota58 atribuye el documento a
Manuel de Vega Bazán, Guañec, 21-02-1822; se verificó esa referencia en el artículo,
sin consultar el manuscrito. La retórica citada no se presenta como hecho probado.

Un sondeo provisional desde la referencia al caso peruano hasta el final de la
cita contiene 133 palabras. No se encontraron coincidencias exactas ni superiores
al umbral léxico entre ese pasaje y los 814 registros actuales. La comprobación
solo usa indicadores de evaluación, sin leer esos textos para etiquetar. Un control
positivo detectó un texto idéntico. Esto no acredita independencia documental ni
novedad del artículo entero; la selección exacta todavía requiere revisión.

La p.132 (PDF8) queda como opción secundaria sobre Cádiz y libertad de imprenta:
su comienzo depende de la p.131 y después deriva hacia infraestructura. No se
etiquetará todo el artículo como crisis e ideas por mencionar prensa o clero.

Otras opciones examinadas:

- [Martínez Riaza, *Libertad de imprenta y periodismo político en el Perú*](https://repositorio.pucp.edu.pe/items/4886bb23-1e37-4584-a5bb-9b964137e6ee/full):
  pertinente y con URI CC BY 4.0 en la ficha completa. Se pospone para cotejar
  edición (ficha 2010 frente a registro original 1984), OCR deteriorado y orden
  de páginas dobles. El intento de captura visual falló; no se descargó localmente.
- [Hampe Martínez (2012), *La “primavera” de Cádiz*](https://www.historiaconstitucional.com/index.php/historiaconstitucional/article/view/336):
  resumen pertinente; la sección Licencia consultada no identifica una licencia
  abierta de reutilización para terceros. Queda pendiente, sin extracción.

Solo se descargó un PDF pequeño. La referencia congelada y la copia corregida
permanecen intactas; no se asignó partición a la nueva fuente, no se incorporaron
filas y no hubo entrenamiento ni solicitudes a Modal. Las valoraciones son
asistidas por IA, no validación humana independiente.

La selección quedó registrada en `e235873`. La preparación y revisión del pasaje
exacto se documenta a continuación.

## Piloto HUE01 de Huerta — registrado en `6c641c3`

[prepare_huerta_pilot.py](../scripts/prepare_huerta_pilot.py) recupera el pasaje de
p.145/PDF21 fijado en la ficha de fuente. Une saltos y guiones de fin de línea y
retira únicamente la llamada 58; conserva la grafía histórica y las mayúsculas.
El resultado tiene **133 palabras** y coincide con la huella del sondeo previo.

El [dictamen del piloto](../artifacts/reviews/huerta-pilot-v1.json) registra la
aprobación temática de ambos agentes como `crisis_ideas_emancipadoras`. El segundo
revisor conocía la propuesta; no es lectura ciega ni validación humana independiente.
Su motivo es el predominio de la justificación religiosa de la emancipación,
frente a la biografía de San Martín o la participación del sacerdote como actor.

La vista legible en `outputs/huerta-pilot-v1/revision-legible.md` distingue el
comentario de Huerta de la cita documental. `candidate.json` conserva el texto,
las páginas de contexto 144–146 y la nota58. Esta atribuye la proclama a Manuel
de Vega Bazán, Guañec, 21-02-1822, AAL, Curas Patriotas, Proclamas, legajo 1,
expediente 1, f.2r–v. Se registra también un grupo documental para reunir futuras
copias o fragmentos de esa misma proclama.

La expresión «grangeárnosla» tiene un antecedente nominal incompleto dentro de
la cita: se conserva con esa observación, sin introducir una palabra supuesta.
El revisor considera interpretable el fragmento con su introducción. No se cotejó
el manuscrito ni una imagen renderizada; el control fue sobre la capa textual.

Verificación: extracción repetida idéntica, separación de comentario/cita,
grafía y atribución preservadas; 814 comparaciones sin coincidencias marcadas y
control positivo de duplicados correcto. Los sondeos de «Manuel de Vega Bazán»,
«Guañec» y «Curas Patriotas» no encontraron coincidencias. Son controles acotados,
no demostración de independencia o ausencia de paráfrasis. También pasaron los
rechazos de hash, extracción, límites, longitud, sobrescritura y ruta.

Reproducción con las entradas locales existentes y un archivo nuevo:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/prepare_huerta_pilot.py --output outputs/huerta-pilot-v1/reproduccion.json
```

Al cerrar ese bloque, el candidato no tenía partición asignada ni se había
incorporado a ningún dataset. El dictamen conserva ese estado histórico.
La incorporación posterior se registra por separado a continuación.

## Copia experimental con HUE01 — registrada en `98874e5`

[build_huerta_snapshot.py](../scripts/build_huerta_snapshot.py) parte de la copia
corregida `outputs/history-corrections-v1/reviewed-export.json` y añade únicamente
HUE01 a entrenamiento. Comprueba las entradas, reproduce la extracción y exige
que texto, etiqueta y procedencia coincidan con el dictamen registrado.
El texto completo queda en `outputs/huerta-snapshot-v1/reviewed-export.json`;
la [evidencia ligera](../artifacts/reviews/huerta-snapshot-v1.json) registra hashes,
recuentos y verificaciones, sin publicar el corpus completo.

Resultado local: **815 filas, 597 train, 81 validación y 137 test**. Crisis e ideas
pasa de 58 a 59 ejemplos de entrenamiento. Las 814 filas de entrada, sus etiquetas
y su orden permanecen idénticos; se conservan AGN01/02, la reparación de Fonseca,
las correcciones R04/R16 y sus registros de procedencia. La referencia congelada
y sus 218 filas de evaluación no cambiaron.

Huerta recibe un identificador de fuente derivado del DOI, asignado a train.
La procedencia conserva además el grupo de la proclama citada, páginas, atribución,
licencia, ajustes de extracción y observaciones de calidad. La cita y el contexto
siguen en `outputs/huerta-pilot-v1/candidate.json`. El informe local señala también
la ubicación y huella del archivo anterior de Fonseca; estos archivos deben
conservarse junto con las versiones locales para poder reconstruir el trabajo.

Verificación: reproducción idéntica de los dos archivos generados, metadatos
anteriores conservados y ausencia de solapamientos marcados para HUE01.
Pasaron 14 controles de rechazo: evaluación alterada, discrepancia de etiquetas,
dictamen no aprobado, texto o contexto alterados, candidato ya asignado o aplicado,
fuente/texto/grupo documental/candidato duplicados, hash inválido, sobrescritura
y salida fuera de `outputs/`. La comparación léxica no demuestra ausencia de
paráfrasis ni independencia documental absoluta.

Reproducción con las entradas locales existentes, hacia una carpeta nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/build_huerta_snapshot.py --output outputs/huerta-snapshot-reproduccion
```

Estado: implementado y ejecutado localmente; sin entrenamiento, métricas nuevas
ni cambios en producción. Se mantiene explícita la revisión asistida por IA,
sin validación humana independiente. El mínimo de cambios del mantenimiento
permanece igual y no se ejecutó el pipeline en este bloque.

La copia quedó registrada en `98874e5`. El lote adicional se describe a continuación;
un ejemplo adicional no permite afirmar una mejora del modelo.

## Tres candidatos adicionales de Huerta — registrados en `1c90715`

[prepare_huerta_batch.py](../scripts/prepare_huerta_batch.py) extrae tres unidades
continuas de la fuente ya descargada. La [revisión del lote](../artifacts/reviews/huerta-batch-v1.json)
registra límites, ajustes, páginas, referencias, hashes y dictámenes. Los textos y
el contexto permanecen en `outputs/huerta-batch-v1/candidates.json`; la vista para
lectura es `outputs/huerta-batch-v1/revision-legible.md`.

| Candidato | Página impresa / PDF | Palabras | Acuerdo temático y cautela |
|---|---|---|---|
| HUE02 | 138 / 14 | 149 | Crisis e ideas, confianza alta: propaganda dirigida a lectores y oyentes. La fecha del periódico es 25-07-1821; la proclama anuncia el día 28 |
| HUE03 | 140 / 16 | 185 | Crisis e ideas, confianza alta: carta de Machado a Diéguez, 14-10-1821, sobre lecturas políticas y derechos. «Esclavitud» forma parte de su retórica política |
| HUE04 | 141 / 17 | 181 | Crisis e ideas, confianza media: prensa fidelista/patriota y restricciones. Cronología resumida y antecedente dependiente de HUE03 |

Ambos agentes aprueban las etiquetas para una incorporación experimental futura.
El segundo propuso límites desde el PDF y después cotejó las selecciones exactas;
conocía el objetivo y la fuente. No es una revisión ciega, humana ni de sistemas
independientes. No se consultaron los originales de la Gaceta o del archivo.

Las tres unidades comparten fuente secundaria con HUE01 y deben permanecer en
train. HUE02 y HUE03 citan documentos distintos de la proclama de Vega Bazán;
HUE04 es una síntesis, no un tercer documento primario independiente. Se conserva
su relación con HUE03. Su enumeración no demuestra que todos esos periódicos
circulasen simultáneamente, antes de la libertad de imprenta o bajo prohibición.
Solo la nota 42 respalda directamente HUE04; las notas 43–44 del contexto pertenecen
al párrafo siguiente.

Se unieron guiones de fin de línea y espacios, se retiraron las llamadas 35, 40,
41 y 42 y se corrigió explícitamente el espaciado «T omás» a «Tomás» en HUE03.
No se modernizaron las citas. El pasaje de Cádiz de pp.131–132 queda como contexto:
tiene 118 palabras; no se añadió material de imprentas para alcanzar el mínimo.

Verificación local: reproducción idéntica, palabras y hashes correctos, contexto
y notas conservados, 815 comparaciones por candidato y tres comparaciones entre
candidatos sin coincidencias marcadas. Pasaron tres controles positivos de
duplicados y nueve rechazos (hash, límites, ajuste, longitud, sobrescritura y ruta).
La ausencia de coincidencias léxicas no demuestra independencia documental.
La referencia congelada y todas las versiones anteriores permanecen intactas.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/prepare_huerta_batch.py --output outputs/huerta-batch-v1/reproduccion.json
```

Al cerrar ese bloque, el lote quedó preparado y revisado localmente, sin filas
nuevas, entrenamiento, descargas ni llamadas a Modal. El dictamen conserva ese
estado histórico; la incorporación se registra por separado a continuación.

## Incorporación del lote HUE02/03/04 — registrada en `b7e7094`

[build_huerta_batch_snapshot.py](../scripts/build_huerta_batch_snapshot.py) añade
el lote completo a la copia que ya contenía HUE01. Reproduce la extracción y
verifica las entradas, el acuerdo de etiquetas y la fuente antes de generar
`outputs/huerta-batch-snapshot-v1/reviewed-export.json`. La
[evidencia de incorporación](../artifacts/reviews/huerta-batch-snapshot-v1.json)
registra resultados, procedencia y hashes sin incluir el corpus completo.

Resultado: **818 filas, 600 train, 81 validación y 137 test**. Crisis e ideas pasa
de 59 a 62 ejemplos en train. Se conservaron las 815 filas anteriores en su orden,
las correcciones y todos los registros de procedencia. La referencia congelada
y sus 218 filas de evaluación permanecen idénticas.

Los nuevos fragmentos usan el mismo identificador de fuente de HUE01 y solo
aparecen en train; el número total de fuentes continúa en 12. La procedencia por
fragmento conserva la relación HUE03/HUE04, sus condiciones históricas, páginas,
referencias, cambios de extracción y acceso al contexto local. Para HUE02 también
se indica el inicio de la cita, distinguiéndolo del análisis de Huerta. Los archivos
de contexto anteriores, incluido el de Fonseca, siguen localizables desde el informe.

Verificación local: reproducción idéntica, conservación de filas y metadatos,
coincidencia de hashes y separación por fuente correctas. Pasaron 17 controles
de rechazo: evaluación alterada, candidato ausente o repetido, texto o contexto
alterados, desacuerdo de etiquetas, candidato no aprobado o ya aplicado, partición
incorrecta del lote o fuente, relación desconocida, incorporación repetida, grupo
documental o texto duplicados, hash inválido, sobrescritura y salida fuera de `outputs/`.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/build_huerta_batch_snapshot.py --output outputs/huerta-batch-snapshot-reproduccion
```

Estado: implementado y probado localmente; sin entrenamiento, métricas nuevas,
cambios del umbral de mantenimiento ni cambios en producción. Las etiquetas
siguen siendo revisiones asistidas por IA, no validación humana independiente.

La incorporación quedó registrada en `b7e7094`. La comparación posterior se
describe a continuación.

## Comparación local del enriquecimiento con Huerta — registrada en `6099156`

[compare_tfidf_validation.py](../scripts/compare_tfidf_validation.py) reutiliza
el entrenamiento TF-IDF y las métricas existentes para comparar una ampliación
de train, sin ejecutar el ciclo completo que también predice sobre test.
Se fijaron **C=4 y semilla 42**, seleccionados en el experimento anterior, antes
de medir esta nueva versión. No se buscaron hiperparámetros nuevos.

Se entrenaron dos modelos en CPU local, con un hilo: la copia corregida anterior
a Huerta (596 train) y la que incluye HUE01/02/03/04 (600 train). Conservan las
mismas 81 filas de validación. El resultado anterior reprodujo exactamente sus
métricas registradas. La [evidencia](../artifacts/experiments/huerta-comparison-v1/comparison.json)
incluye parámetros, hashes, versiones, métricas por clase y matrices de confusión.
Los modelos y las predicciones locales quedan excluidos de Git en
`outputs/huerta-comparison-v1/`.

| Métrica de validación | Antes de Huerta | Con Huerta |
|---|---:|---:|
| F1 macro | 0.29004 | 0.28968 |
| Exactitud | 0.30864 | 0.30864 |
| Aciertos / total | 25 / 81 | 25 / 81 |
| F1 crisis e ideas, 15 casos | 0 | 0 |

**No se observó mejora.** La variación de F1 macro es −0.00036, equivalente a
−0.036 puntos porcentuales. Cambió una predicción incorrecta por otra incorrecta:
un caso de crisis e ideas pasó de organización republicana a contexto colonial.
No se interpreta esa diferencia pequeña como evidencia de significancia estadística.

Esta comparación no evalúa BETO, que continúa en producción. Tampoco demuestra
que enriquecer datos sea inútil: solo se añadieron cuatro pasajes de una misma
fuente secundaria. Validación contiene una sola fuente y ya se utilizó antes;
no es una evaluación externa nueva. Test se conservó para las comprobaciones de
integridad del dataset, sin predicciones ni métricas nuevas en este bloque.

Verificación: las métricas se recalcularon desde las predicciones guardadas,
ambos modelos convergieron y reprodujeron las predicciones después de recargarlos.
Se verificó que las únicas diferencias entre los datos fueran las cuatro filas
añadidas a train; referencia, evaluación y entradas permanecieron intactas.
Pasaron nueve rechazos: modificación de filas existentes, filas nuevas fuera de
train, ausencia de ampliación, hiperparámetros alterados, otro tipo de modelo,
selección desconocida, selección por test, sobrescritura y salida fuera de `outputs/`.

Reproducción hacia una carpeta local nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/compare_tfidf_validation.py --before outputs/history-corrections-v1/reviewed-export.json --after outputs/huerta-batch-snapshot-v1/reviewed-export.json --config configs/experiments/tfidf.json --selection outputs/history-comparison-v1/reviewed/selection.json --output outputs/huerta-comparison-reproduccion
```

Estado: ejecutado y verificado localmente, sin gastos remotos ni despliegues.
Se conservan los datos revisados como experimentales; no se revierten etiquetas
históricamente justificadas para buscar una puntuación mayor.

La comparación quedó registrada en `6099156`. El diagnóstico siguiente se centra
en entrenamiento, conservando la evaluación congelada.

## Diagnóstico de cobertura y fronteras temáticas — registrado en `afd742e`

[diagnose_training_coverage.py](../scripts/diagnose_training_coverage.py) resume
las 600 filas de train, su distribución por fuente, longitud y duplicados, y
consulta los coeficientes del modelo local ya entrenado. No realiza predicciones
ni entrenamiento. La [evidencia del diagnóstico](../artifacts/reviews/coverage-diagnosis-v1.json)
conserva recuentos, hashes y cinco casos que requieren contexto.

| Hallazgo | Evidencia | Alcance de la conclusión |
|---|---|---|
| Concentración de crisis e ideas | 47/62 ejemplos (75.8%) provienen de O'Phelan y un video; seis fuentes en total para esta clase | Hay poca diversidad entre muchos de sus ejemplos; no demuestra por sí sola la causa del fallo |
| Concentración de organización republicana | 86/101 ejemplos (85.1%) provienen de dos fuentes | También esta clase depende mucho de determinadas fuentes |
| Rasgos de transcripción | «eh» y «de de» figuran entre los 15 coeficientes positivos mayores de crisis e ideas; aparecen en 17 y 11 filas de esa clase | Posible asociación con estilo de fuente; los coeficientes no son probabilidades ni explican por sí solos una predicción |
| Unidades PDF cortas | 87/528 filas PDF tienen menos de 120 palabras: 53 son `no_relevante` y 34 pertenecen a clases históricas | Señal para revisión; no eliminar automáticamente negativos ni fragmentos interpretables |

Se conserva el duplicado conocido de train, ahora en índices 715/743 por los
cambios anteriores de orden. No se eliminó en este diagnóstico.

Para la revisión temática se eligieron hasta dos filas por fuente y etiqueta
de las clases ideas/organización, por orden SHA-256 fijo: 21 filas de train.
El segundo agente revisó esta muestra con etiquetas visibles; no constituye
validación humana independiente ni permite estimar la tasa de error del corpus.
La vista local de los cinco casos está en `outputs/coverage-diagnosis-v1/revision-legible.md`.

Los índices 633 y 15 del artículo de Carmen Villanueva muestran una comparación
constitucional partida entre las páginas PDF1–2, impresas427–428. Ambos agentes
comprobaron esa continuidad en `.corpus-downloads/constitucion_1823.pdf`.
Antes de juzgar sus etiquetas, conviene reconstruir los argumentos y contrastarlos
con las filas 7 y 14. El índice80 plantea una frontera entre ideas y conflicto de
tierras; el 28 mezcla descripción económica con notas; el 693 requiere audio y
contexto para distinguir trayectoria personal de organización estatal. Son casos
para seguimiento, no correcciones aprobadas.

Verificación: recuentos conciliados, muestra reproducida y hashes comprobados;
alterar en memoria los textos y etiquetas de evaluación no cambia el diagnóstico
de train. Pasaron los rechazos de sobrescritura, salida fuera de `outputs/` y
dataset distinto del utilizado por el modelo. Las entradas permanecieron intactas.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/diagnose_training_coverage.py --dataset outputs/huerta-batch-snapshot-v1/reviewed-export.json --model-report outputs/huerta-comparison-v1/report.json --output outputs/coverage-diagnosis-v1/reproduccion.json
```

Estado: diagnóstico local completado, sin métricas nuevas, cambios de etiquetas,
descargas ni cambios en producción. Siguiente paso después del commit: revisar
únicamente las filas **7, 633, 15 y 14 de Villanueva**, recuperar su continuidad
y proponer límites argumentales con evidencia antes de modificar el dataset.

## Límites argumentales de Villanueva — registrados en `f2d96c6`

El [mapa de límites](../artifacts/reviews/villanueva-boundaries-v1.json) coteja
las filas 7, 633, 15 y 14 con las páginas PDF 1–5 (impresas 427–431) del artículo
de Carmen Villanueva, *La Constitución de 1823 y los inicios de la República*,
BIRA 23 (1996). Las etiquetas y el dataset permanecen intactos.

| Unidad | Contenido delimitado | Palabras | Tratamiento en esta propuesta |
|---|---|---|---|
| V01 | Introducción sobre la Constitución de 1823 | 82 | Conservar como contexto |
| V02 | Experiencias liberales y antecedentes peruanos | 178 | Revisar frontera entre ideas y organización constitucional |
| V03 | Comparación constitucional de Perú, Argentina y Colombia | 145 | Reúne la oración cortada entre PDF 1–2; etiqueta pendiente |
| V04 | Propuestas políticas de Bolívar y Carta de Jamaica | 175 | Incluye continuación que ya pertenece a la fila 637 |
| V05 | Cierre de la discusión sobre monarquismo | 61 | Conservar como contexto |
| V06 | Formación y composición del Congreso | 163 | Completa PDF 4–5 con prosa que ya pertenece a la fila 10 |

Estas unidades son un mapa argumental, **no seis ejemplos aprobados**. No se
rellenan los pasajes breves ni se los convierte automáticamente en `no_relevante`.
Se unieron espacios y límites de página; se conservaron grafías de extracción y
llamadas de notas para revisarlas antes de preparar candidatos definitivos.
La fila 15 y la 14 no son consecutivas en el documento: entre ambas hay discusión
de Burke, Santander, San Martín y monarquismo que no se debe omitir como si fuera
una transición inmediata.

El segundo agente propuso los límites; el agente principal reprodujo las seis
extracciones y comprobó que las continuaciones están en las filas 10 y 637.
Ambos leyeron la guía y la capa de texto del PDF. Es revisión asistida por IA,
con etiquetas visibles; no constituye validación humana independiente ni cotejo
de los documentos históricos originales que cita Villanueva.

Verificación local: marcadores únicos, recuentos reproducidos, hashes del PDF y
dataset comprobados, solapamientos con 10/637 confirmados y entradas intactas.
Los textos completos y el script auxiliar local están en
`outputs/villanueva-boundaries-v1/`, excluidos de Git. No hubo entrenamiento,
métricas nuevas ni cambios en producción.

Siguiente bloque después del commit: preparar un reemplazo reversible que
considere las seis filas implicadas (7, 633, 15, 14, 10 y 637), conservando los
originales y el texto restante de 10/637. Revisar etiquetas y ajustes de extracción
antes de incorporar candidatos; no añadir continuaciones duplicando las existentes.

## Propuesta de reparación de Villanueva — registrada en `e0e0b3d`

[prepare_villanueva_repair.py](../scripts/prepare_villanueva_repair.py) reproduce
los límites revisados y prepara la [propuesta trazable](../artifacts/reviews/villanueva-repair-v1.json).
No escribe un dataset nuevo ni modifica el actual. Los seis originales (7, 633,
15, 14, 10 y 637) se conservan íntegros, con una partición de cada carácter que
indica su destino: candidato, contexto o paratexto.

| Unidad | Palabras | Decisión propuesta tras revisión |
|---|---|---|
| V03 | 145 | Organización y consecuencias republicanas: comparación constitucional |
| V04 | 175 | Liderazgos, diplomacia y proyectos: pensamiento político de Bolívar |
| V06 | 163 | Organización y consecuencias republicanas: formación del Congreso |
| V07 | 142 | Organización y consecuencias republicanas: Bases y preparación constitucional, resto de fila 10 |

V01 (82 palabras), V05 (61) y V08 (25, resto incompleto de fila 637) se conservan
como contexto. **V02 (178) queda ambiguo**: el principal favoreció ideas, mientras
el segundo agente no encontró predominio suficiente sobre los antecedentes
constitucionales. Se registra el desacuerdo y no se fuerza una etiqueta.
V03 conserva V02 como contexto asociado. No se amplía V08 hacia la fila 651.

Se retiraron las llamadas de notas 1/2 de V04 y 7 de V07, conservando sus referencias
y texto original. El cierre `asequible2• → asequible.` incluye normalización
editorial de puntuación, sin cotejo visual. Se conservan y señalan `Tarrna`,
`mayore s` y el apóstrofo aislado de V03. La revisión temática es asistida por IA;
no certifica los hechos citados ni sustituye validación humana independiente.

Verificación local: preparación reproducida exactamente; originales reconstruidos
sin pérdida; todas las unidades conservan la secuencia de letras y números de sus
pasajes originales antes de los ajustes documentados. No hay duplicados exactos
ni coincidencias por encima del umbral de cinco palabras entre candidatos o con
las 594 filas restantes de train. El umbral no garantiza ausencia de todo solapamiento.
Pasaron ocho rechazos, incluidos marcadores inválidos, particiones incompletas,
manifiesto alterado, sobrescritura y salida fuera de `outputs/`. PDF y datasets intactos.

Los textos, páginas, originales y comprobaciones están en
`outputs/villanueva-repair-v1/`, excluido de Git. Para reproducir en un archivo nuevo:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/prepare_villanueva_repair.py --output outputs/villanueva-repair-reproduccion/proposal.json
```

Siguiente bloque después del commit: incorporar el reemplazo en **otra copia
experimental local**, con su archivo de originales y contexto. La proyección es
600 → 598 filas de train: retirar seis originales e incorporar cuatro candidatos;
validación (81) y test (137) deben permanecer idénticos. Esa incorporación todavía
no ocurrió. No hay entrenamiento, métricas nuevas ni cambios en producción.

## Copia experimental con la reparación de Villanueva — registrada en `1f5f6fd`

[build_villanueva_snapshot.py](../scripts/build_villanueva_snapshot.py) aplica
la propuesta revisada en una carpeta local nueva. La [evidencia de incorporación](../artifacts/reviews/villanueva-snapshot-v1.json)
registra hashes, recuentos, comprobaciones y ubicación de los archivos.

Se sustituyeron las filas del padre 7, 633, 15, 14, 10 y 637 por V03, V04, V06 y
V07. El resultado contiene **816 filas: 598 train, 81 validación y 137 test**.
Las otras 812 filas conservaron texto, etiqueta, fuente, partición y orden.
Los 218 ejemplos de evaluación coinciden exactamente con la referencia congelada.

El archivo `outputs/villanueva-snapshot-v1/replacement-archive.json` conserva
las seis filas originales, sus particiones completas, las ocho unidades extraídas
y siete páginas de contexto/notas. V01, V02, V05 y V08 quedan fuera del entrenamiento;
V02 conserva el desacuerdo histórico, y V03 lo referencia como contexto asociado.
La prosa usada para entrenar se reduce: no se presenta esta reparación como una
ampliación del corpus ni como mejora demostrada del modelo.

Se conservaron el historial de correcciones, la procedencia de AGN/Huerta/Fonseca
y la referencia al archivo anterior de Fonseca. Se añadió procedencia específica
para los cuatro candidatos, incluidos sus ajustes de extracción, advertencias y
origen de revisión asistida por IA. La fuente continúa exclusivamente en train.
El duplicado conocido fuera de este grupo sigue intacto.

Verificación: los tres archivos se reprodujeron exactamente; archivo de originales
sin pérdida, metadatos anteriores conservados y evaluación idéntica. Pasaron 14
rechazos: cambios de evaluación/taxonomía, originales/candidatos alterados, grupo
incompleto, contexto ambiguo etiquetado, archivo incompleto, fuente distinta,
revisión ya aplicada o alterada, solapamiento fuera del grupo y salidas inválidas.
Las operaciones fallidas no modificaron sus entradas.

Para reproducir en una carpeta nueva:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/build_villanueva_snapshot.py --output outputs/villanueva-snapshot-reproduccion
```

Estado: incorporación local completada; dataset anterior y referencia intactos.
No se entrenó ni desplegó un modelo. Siguiente bloque después del commit: comparar
el efecto de esta sustitución con TF-IDF local y configuración fija, usando solo
validación. El comparador anterior supone adiciones; habrá que admitir esta
sustitución auditada conservando sus controles de evaluación y procedencia.

## Comparación de la reparación de Villanueva — registrada en `719a287`

Se amplió [compare_tfidf_validation.py](../scripts/compare_tfidf_validation.py)
para aceptar una sustitución respaldada por su evidencia y un informe previo.
Verifica las huellas de ambas versiones, la evaluación intacta, los archivos de
procedencia y la misma configuración. Conserva el modo anterior para adiciones.
La versión anterior debe reproducir sus métricas registradas antes de comparar.

La [evidencia de comparación](../artifacts/experiments/villanueva-comparison-v1/comparison.json)
registra dos entrenamientos locales TF-IDF con **C=4 y semilla 42**, sin búsqueda
nueva de hiperparámetros. Se utilizó un hilo de CPU; cada ajuste con predicción
tardó aproximadamente 0.7 segundos, sin incluir importaciones y comprobaciones.

| Métrica en los mismos 81 ejemplos de validación | Antes, 600 train | Después, 598 train |
|---|---|---|
| F1 macro | 0.28968 | 0.28987 |
| Exactitud | 0.30864 | 0.30864 |
| Aciertos | 25 | 25 |
| F1 de crisis e ideas, 15 casos | 0 | 0 |

Solo cambió una predicción: un ejemplo etiquetado como crisis e ideas pasó de
participación social a organización republicana; siguió siendo incorrecto.
Ninguna versión predijo la clase crisis e ideas en validación. El incremento de
F1 macro de 0.00019 no demuestra mejora práctica ni significación estadística.
No permite atribuir el efecto por separado a extracción, etiquetas o contexto retirado.

Verificación: métricas anteriores reproducidas, ambos modelos guardados recargados
con las mismas 81 predicciones y métricas por clase/matrices recalculadas. Pasaron
15 rechazos, incluidos cambios en train/evaluación, sustitución sin evidencia,
configuración o informe anterior incompatibles y salidas inválidas. Se comprobó
también compatibilidad con las entradas del experimento anterior de adiciones.
Los modelos y predicciones completos quedan en `outputs/villanueva-comparison-v1/`.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/compare_tfidf_validation.py --before outputs/huerta-batch-snapshot-v1/reviewed-export.json --after outputs/villanueva-snapshot-v1/reviewed-export.json --config configs/experiments/tfidf.json --selection outputs/history-comparison-v1/reviewed/selection.json --replacement-evidence artifacts/reviews/villanueva-snapshot-v1.json --previous-report artifacts/experiments/huerta-comparison-v1/comparison.json --output outputs/villanueva-comparison-reproduccion
```

Estado: comparación local completada, sin predicciones de test, entrenamiento de
BETO ni cambios en producción. Validación contiene una sola fuente y ya se usó
para selección y comparaciones; no constituye evaluación externa nueva.
Siguiente bloque después del commit: evaluar la generalización entre fuentes con
particiones internas de train, dejando una fuente fuera cada vez. Esto permitirá
orientar el próximo experimento conservando intacta la evaluación congelada.

## Bloque actual: generalización entre fuentes de train

[evaluate_tfidf_by_source.py](../scripts/evaluate_tfidf_by_source.py) realiza nueve
rondas: en cada una deja fuera una fuente de train, aprende vocabulario y modelo
desde cero con las otras ocho y predice exclusivamente la fuente excluida.
Se conserva TF-IDF con C=4, semilla 42 y un hilo de CPU. Cada una de las 598 filas
de train se evalúa una sola vez; no se predicen validación ni test.

La [evidencia del diagnóstico](../artifacts/experiments/source-generalization-v1/report.json)
registra modelos, particiones, clases, métricas y comprobaciones.

| Fuente excluida del entrenamiento | Ejemplos evaluados | Exactitud | Aciertos de ideas / ejemplos de ideas |
|---|---:|---:|---:|
| O'Phelan | 103 | 40.78% | 0/28 |
| AGN | 2 | 50.00% | — |
| Huerta | 4 | 0.00% | 0/4 |
| Video de train | 72 | 29.17% | 2/19 |
| Basadre | 244 | 28.28% | 3/6 |
| Villanueva | 16 | 56.25% | — |
| Orrego | 53 | 26.42% | — |
| Huamanga | 58 | 55.17% | 0/3 |
| Fonseca | 46 | 43.48% | — |

El agregado de las 598 predicciones obtuvo **F1 macro 0.32372 y 208 aciertos
(34.78%)**. Crisis e ideas tuvo F1 0.11364 y 5/60 aciertos; contexto colonial,
F1 0.08163 y 6/71. La referencia que predice la clase mayoritaria de las fuentes
de entrenamiento obtuvo F1 macro 0.02394 y exactitud 4.18%. Superar esa referencia
simple no demuestra que el clasificador sea suficientemente bueno para el uso final.

Estos resultados señalan dificultades para transferir lo aprendido entre fuentes,
sin demostrar una causa única. **0.32372 no es una mejora sobre la validación
anterior**: se evaluaron otros ejemplos y nueve modelos. Tampoco es una estimación
final independiente: los datos fueron revisados y los parámetros ya se eligieron
con la validación original. No se deben ordenar fuentes por calidad usando esta tabla;
algunas tienen solo dos o cuatro ejemplos y distintas distribuciones de clases.
El agregado pondera filas: Basadre aporta 244/598. El F1 macro de cada ronda usa
siempre las siete clases, incluso las ausentes de esa fuente.

Verificación: nueve modelos guardados reprodujeron sus predicciones; vocabulario
y valores IDF se comprobaron contra las filas de entrenamiento de cada ronda.
Métricas agregadas, por fuente y de la referencia mayoritaria recalculadas. Pasaron
11 rechazos, incluidos mezcla con evaluación, fuente única, clases ausentes del
entrenamiento, duplicados entre fuentes, configuración incompatible y salidas
inválidas. El duplicado conocido dentro de una misma fuente permanece unido.
Cambiar en memoria textos y etiquetas de validación/test no altera estas rondas.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/evaluate_tfidf_by_source.py --dataset outputs/villanueva-snapshot-v1/reviewed-export.json --config configs/experiments/tfidf.json --selection outputs/history-comparison-v1/reviewed/selection.json --previous-report artifacts/experiments/villanueva-comparison-v1/comparison.json --output outputs/source-generalization-reproduccion
```

Estado: diagnóstico local completado. Los nueve modelos y predicciones están en
`outputs/source-generalization-v1/`, excluidos de Git; producción permanece intacta.
Siguiente bloque después del commit: comparar representaciones de palabras y
secuencias de caracteres con las mismas rondas internas y configuración fija del
clasificador. Será una prueba de representación del texto, conservando etiquetas
y evaluación congelada, sin prometer una mejora.

### Reproducir la muestra de la revisión inicial

Reproducir la muestra en un archivo local nuevo desde la raíz (no sobrescribe):

```powershell
outputs/venv-ml/Scripts/python.exe scripts/sample_history_review.py --output outputs/history-review-v1/sample-reproduced.json --include-text
```

El script usa solo la biblioteca estándar de Python y no consulta servicios.
El JSON versionado contiene las justificaciones; `outputs/history-review-v1/revision-legible.md`
reúne localmente textos y decisiones para revisarlos con comodidad.

Comprobación local realizada: 20 registros únicos, cuotas por clase correctas,
selección determinista, pertenencia exclusiva a train, hashes y etiquetas originales
coincidentes con el snapshot, conteos de decisiones consistentes y dataset intacto
byte a byte. También se comprobó el rechazo de muestras insuficientes, taxonomías
incompatibles, sobrescrituras y salidas con texto fuera de `outputs/`.
`git diff --check` pasó y las dos vistas locales quedaron excluidas por `.gitignore`.

La muestra inicial quedó registrada en `95e9dd1`; sus decisiones no fueron aplicadas.
La prueba visual de producción sigue pendiente en paralelo.

## Qué debes poder explicar

1. El modelo recibe **texto de un fragmento**, tokenizado en subpalabras, truncado a 192 tokens, con máscara de atención. Predice una de siete clases.
2. BETO usa representaciones aprendidas del texto. Años, personas y lugares son salidas adicionales: no son automáticamente las variables de entrada del clasificador.
3. TF-IDF representa palabras y bigramas; la regresión logística sirve como comparación económica.
4. Train ajusta pesos; validación selecciona hiperparámetros y época; test mide el resultado de la selección terminada.
5. La separación por fuente evita que páginas o fragmentos del mismo material aparezcan a ambos lados de la evaluación. También se rechazan duplicados de texto entre conjuntos.
6. F1 macro promedia el F1 de todas las clases con igual peso. No es porcentaje de respuestas correctas; ese porcentaje se mide con accuracy.
7. CI verifica cambios de software. Mantenimiento ML produce y evalúa candidatos a partir de datos versionados. Son flujos relacionados pero distintos.
8. Un candidato entrenado no se convierte por sí solo en el modelo activo de producción.

## Ejecutar los experimentos en este equipo

Se creó `outputs/venv-ml` porque el entorno anterior referencia un Python inexistente.
Los resultados grandes permanecen en `outputs/`, excluido de Git. No se modificó `.gitignore`.

Desde PowerShell, en la raíz:

```powershell
$env:PYTHONPATH = 'apps/ml'
outputs/venv-ml/Scripts/python.exe -m app.ml.experiments --dataset artifacts/datasets/gold-v1-source-aware.json --config configs/experiments/tfidf.json --output outputs/experiments/tfidf-nueva-ejecucion
outputs/venv-ml/Scripts/python.exe -m app.ml.experiments --dataset artifacts/datasets/gold-v1-source-aware.json --config configs/experiments/beto.json --output outputs/experiments/beto-nueva-ejecucion
```

La carpeta de salida debe ser nueva para conservar la evidencia previa. Cada ejecución guarda auditoría, parámetros, selección, métricas finales, dependencias y candidato. Los experimentos BETO requieren CUDA por defecto; el perfil usa microbatches de 2 y acumulación de 8 (batch efectivo 16), precisión mixta y gradient checkpointing.

Para reproducir el entorno en otro equipo con GPU compatible:

```powershell
python -m venv outputs/venv-ml
outputs/venv-ml/Scripts/python.exe -m pip install -r apps/ml/requirements-test.txt
outputs/venv-ml/Scripts/python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
outputs/venv-ml/Scripts/python.exe -m pip install -r apps/ml/requirements-experiments.txt
```

El índice CUDA depende del hardware/controlador; la receta se basa en los [binarios oficiales de PyTorch](https://pytorch.org/get-started/previous-versions/). Las versiones efectivamente utilizadas quedan registradas en `report.json`.

## Workflows preparados

- **CI**: API tests/build, web lint/build y ML tests. `Quality gate` falla si cualquiera falla o no termina correctamente. Los resultados ML quedan como artefacto JUnit.
- **ML maintenance**: ejecuta el experimento por cambios de datos/configuración, manualmente o cada semana. Por defecto utiliza TF-IDF en CPU. BETO requiere un runner configurado con etiquetas `self-hosted`, `ml-gpu`; puede seleccionarse manualmente o mediante la variable `ML_BACKEND=beto`. No se ha registrado un runner en este trabajo.
- **Production smoke**: comprueba API+ML, autenticación, acceso a proyectos, abstención y HTML web. Se ejecuta manualmente o diariamente; archiva un JSON incluso cuando detecta fallos. Esto es monitorización, todavía no verificación del commit recién desplegado.

El workflow de mantenimiento comienza desde el snapshot académico versionado. Si se configura `ML_REVIEWED_SNAPSHOT` con la ruta de un export completo y revisado, prepara un snapshot nuevo conservando intactas las fuentes de validación/test y entrena solo si hay al menos 20 altas, retiros o cambios de etiqueta en train. `ML_REFERENCE_SNAPSHOT` permite fijar la referencia anterior. Sin export revisado, el workflow repite el experimento académico para verificar reproducibilidad.

**Todavía falta extraer automáticamente las correcciones desde producción** y comparar el candidato con el activo antes de promoverlo. El umbral de cambios se calcula respecto a la referencia configurada: tras aceptar una nueva versión debe actualizarse esa referencia para no repetir su entrenamiento.

Prueba ejecutable sin cambios:

```powershell
$env:PYTHONPATH = 'apps/ml'
outputs/venv-ml/Scripts/python.exe -m app.ml.maintenance --reference artifacts/datasets/gold-v1-source-aware.json --reviewed artifacts/datasets/gold-v1-source-aware.json --config configs/experiments/tfidf.json --output outputs/maintenance-nueva-comprobacion
```

Debe producir `status: skipped` y no entrenar. El export revisado debe contener todo el conjunto aprobado, porque omitir un ejemplo de train significa retirarlo. Las etiquetas revisadas de fuentes reservadas para evaluación no se incorporan al entrenamiento.

`render.yaml` incorpora `autoDeployTrigger: checksPass`, opción documentada por [Render](https://render.com/docs/blueprint-spec#autodeploytrigger). Debe sincronizarse o configurarse en Render y verificarse allí. No se ha cambiado la configuración del servicio remoto. Vercel requiere su propio control para impedir que despliegue antes de CI.

## Tres casos para Unidad II

| Caso | Acción | Evidencia necesaria |
|---|---|---|
| Cambio válido | Ejecutar CI con una modificación válida y desplegar ese commit | URL de la ejecución verde, SHA desplegado y smoke posterior |
| Fallo detectado | Introducir un fallo controlado en una rama de demostración | Ejecución roja y evidencia de que producción conserva el commit anterior |
| Mantenimiento ML | Procesar un snapshot nuevo y evaluar candidato | Huella del dataset, parámetros, métricas, candidato registrado y decisión justificada |

Los tests locales ya comprueban que un dataset con fuga de fuentes se rechaza, que test no decide el ganador y que no se promueve un candidato que incumple los criterios. Estos controles no sustituyen los tres casos remotos.

## Pendientes para completar el ciclo

- [x] Ejecutar y archivar la comparación BETO: candidato seleccionado F1 test 0.31066, permanece experimental.
- [x] Verificar carga e inferencia con pesos reales y conservación del modelo ante una carga fallida (FastAPI local).
- [ ] Repetir recorrido real PDF/YouTube → predicción → corrección persistida.
- [ ] Confirmar si la exigencia de inglés alcanza también a la interfaz.
- [x] Publicar los cambios y conservar URLs de GitHub Actions.
- [ ] Conectar snapshots de correcciones, identidad estable de evaluación y detección de cambios.
- [ ] Guardar pesos BETO en almacenamiento accesible al servicio ML: un artefacto de Actions por sí solo no es una ruta de Modal.
- [ ] Comparar candidato y activo, verificar carga y hacer activación recuperable.
- [ ] Resolver consistencia entre modelo activo de la BD y modelo incorporado en la imagen Modal al reiniciar.
- [ ] Verificar despliegue del SHA correcto y recuperación para API, web y modelo.
- [ ] Ejecutar los tres casos y terminar informe final.

No es necesario incorporar MLflow, Airflow o un feature store independiente para cumplir la rúbrica. El repositorio ya posee registro de modelos y almacenamiento de vectores; primero conviene completar y demostrar su ciclo.

## Evidencia de esta sesión

- Resultados: [TF-IDF](../artifacts/experiments/course-u1/tfidf/report.md) y [BETO](../artifacts/experiments/course-u1/beto/report.md).
- [Pruebas funcionales con pesos reales](../artifacts/experiments/course-u1/evidence/model-functional.json): autenticación interna, carga/inferencia y fallo de reemplazo sin pérdida del modelo cargado.
- [Comprobación de producción](../artifacts/experiments/course-u1/evidence/production-smoke.json): frontend correcto; API/login agotaron el tiempo de espera.
- [Recuperación de producción](recuperacion-produccion.md): posteriormente pasaron las seis comprobaciones; BETO v1 y embeddings cargados. Corrección preventiva de liveness preparada y pendiente de despliegue.
- [Mantenimiento sin cambios](../artifacts/experiments/course-u1/evidence/maintenance-no-changes.json): se omitió entrenamiento.
- Los tres workflows pasaron validación estática con actionlint 1.7.12. Los checks locales no demuestran que GitHub haya ejecutado los workflows nuevos.

## Verificación tras publicar `3974f4a`

El 7 de septiembre de 2026 a las 04:08 UTC se verificaron las ejecuciones disparadas por el push:

- [CI correcto](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34081879616): API, web, ML y Quality gate terminaron con éxito.
- [Mantenimiento correcto](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34081879646): se repitió el experimento TF-IDF sobre el snapshot académico. Se seleccionó C=4, con F1 macro de test 0.363; se archivaron informes y candidato. Producción no fue modificada por este workflow. Esto aún no demuestra reentrenamiento automático desde correcciones.
- [Comprobación de producción posterior](../artifacts/experiments/course-u1/evidence/production-smoke-post-push.json): las seis comprobaciones pasaron desde este equipo. No equivale a una ejecución del workflow Production smoke en GitHub, que continúa pendiente.
- `/api/health/live` respondió HTTP 200 con `status: ok` y `service: api`. Esto confirma que la ruta está disponible, pero no identifica el SHA exacto ni confirma la configuración del health check en el panel de Render.
- Vercel reportó éxito mientras CI seguía en curso. Falta configurar y demostrar que el despliegue espere a CI.

Los estados y SHA de las ejecuciones se conservan en [github-actions-post-push.json](../artifacts/experiments/course-u1/evidence/github-actions-post-push.json). Siguiente bloque: verificar el recorrido fuente → predicción → corrección persistida en producción.

### Incidencia al verificar el recorrido PDF

El 7 de septiembre de 2026 a las 04:11 UTC se creó el proyecto privado de prueba `9676bb4a-1e6d-44a5-9154-17814af4427e`. La carga de un PDF sintético de 2 511 bytes devolvió HTTP 500 y el proyecto quedó sin recursos. El extractor local pudo leer las tres páginas y generar tres segmentos. No se llegó a ejecutar procesamiento remoto ni revisión; no se modificaron fuentes existentes.

Además, la descarga del PDF existente `9154f7f7-86c9-4bad-bcba-47eaf54b93e1`, registrado con proveedor S3, devolvió HTTP 404. Los logs aportados de Render muestran `DatabaseTimeout` tanto al cargar como al descargar: el servicio S3 devolvió un timeout de su base de datos. La descarga repetida a las 04:14 UTC volvió a fallar. No se ha demostrado que el archivo esté eliminado ni que las credenciales sean incorrectas. Evidencia: [source-flow-failed.json](../artifacts/experiments/course-u1/evidence/source-flow-failed.json).

Se preparó una corrección local: los fallos de almacenamiento devuelven HTTP 503 con un mensaje claro; una descarga solo devuelve 404 por archivo ausente (`NoSuchKey` o `ENOENT`) o por referencia inexistente. Seis pruebas nuevas y la compilación pasaron. Esto no restaura el servicio de Supabase y aún no está desplegado.

[Supabase documenta DatabaseTimeout](https://supabase.com/docs/guides/storage/debugging/error-codes) como timeout al acceder a la base de datos de Storage. La causa operativa exacta sigue pendiente. El navegador integrado no estuvo disponible, por lo que la verificación visual sigue pendiente.

Actualización a las 04:17 UTC: la autora mostró el bucket con archivos en el panel de Supabase. La descarga repetida del PDF existente respondió 200. El PDF sintético se cargó en el proyecto de prueba y produjo tres segmentos con referencias de página, pero sin etiquetas sugeridas. El recurso privado es `f81c491d-766a-4a2d-8cb5-ae86ea5b7b25`; no debe incluirse en el corpus histórico.

La reclasificación devolvió «No hay modelo activo cargado». La consulta autenticada a Modal mostró BETO con `ready: false`, `status: error` y un fallo al importar `AutoModelForSequenceClassification` desde `transformers`. Embeddings y NER figuraban cargados. No se cambió el modelo ni se desplegó código durante estas comprobaciones. Evidencia: [source-flow-storage-recovered.json](../artifacts/experiments/course-u1/evidence/source-flow-storage-recovered.json).

El diagnóstico continuó con el arranque de BETO y la revisión del PDF de prueba, como se describe a continuación.

### Arranque de BETO y revisión persistida

En un nuevo arranque de Modal, BETO cargó sin cambiar sus pesos ni desplegar código. Se verificaron en el contenedor `transformers 4.57.6`, `torch 2.12.0+cpu` y `sentence-transformers 5.1.2`; la importación del clasificador funcionó en una comprobación separada. El error anterior fue intermitente. La carga en segundo plano permitía que peticiones concurrentes importaran las mismas dependencias; este es un riesgo identificado, no una causa reproducida de forma concluyente.

Se preparó una corrección local para terminar la carga de BETO durante el arranque ASGI antes de aceptar solicitudes. Si falla el modelo configurado, el arranque falla explícitamente y registra la excepción. También se fijó `transformers==4.57.6`, la versión observada en el contenedor. Las cinco pruebas nuevas y la suite ML completa (42 pruebas) pasaron. Se verificó además arranque e inferencia con pesos reales del candidato local, simulando solamente la descarga: [beto-startup-local.json](../artifacts/experiments/course-u1/evidence/beto-startup-local.json). Falta desplegar y probar esta corrección en Modal.

En producción, la reclasificación del PDF privado existente obtuvo tres predicciones. Se confirmó `no_relevante` en la página 3 y se comprobó su persistencia desde una sesión autenticada nueva. El archivo descargado coincidió byte por byte con el PDF cargado. [Evidencia del recorrido con reintento](../artifacts/experiments/course-u1/evidence/source-flow-reviewed.json). La revisión confirmó una etiqueta ya correcta; no demuestra la corrección de una predicción equivocada. El primer intento de clasificación falló, por lo que no se declara aprobada la ejecución automática completa.

Las correcciones quedaron registradas en `24f03be` (ML) y `0bc365a` (API). Siguiente paso: registrar estas evidencias, publicar los commits y, con autorización de la autora, desplegar ML y verificar un arranque nuevo con predicción automática. Permanecen pendientes la corrección de una etiqueta distinta y la comprobación visual de la interfaz.

## Despliegue automático de Modal

La autora desplegó manualmente la versión Modal v7 el 6 de septiembre de 2026 a las 23:34 en Lima. Se comprobó BETO listo, tres predicciones sobre el PDF privado y conservación de la revisión anterior. El historial de ese despliegue no registró un SHA de Git.

El nuevo workflow `.github/workflows/modal-deploy.yml` automatiza el siguiente ciclo:

1. Esperar una ejecución correcta de CI en `main`, originada por push o ejecución manual de CI. No despliega pull requests.
2. Descargar exactamente el commit que CI verificó. Si `main` ya avanzó, omitir ese despliegue antiguo.
3. Comprobar secretos, desplegar con Modal 1.5.5 y etiquetar la versión con el SHA. Los despliegues de este workflow se serializan.
4. Consultar `/health` y `/infer` con autenticación. Ambas respuestas deben identificar el SHA esperado; BETO debe estar listo y producir una predicción válida.
5. Archivar el resultado JSON durante 90 días. Si la verificación falla, el workflow falla; todavía no restaura automáticamente la versión anterior.

Antes de publicar este workflow, configurar en **GitHub → repositorio → Settings → Secrets and variables → Actions → New repository secret**:

| Nombre exacto | Procedencia y uso |
|---|---|
| `MODAL_TOKEN_ID` | ID de un token de API de [Modal Settings → Tokens](https://modal.com/settings/tokens); permite desplegar |
| `MODAL_TOKEN_SECRET` | Secreto correspondiente al token de API anterior |
| `MODAL_PROXY_TOKEN_ID` | Mismo valor que usa Render para acceder al servicio ML |
| `MODAL_PROXY_TOKEN_SECRET` | Mismo valor que usa Render para autenticar el proxy ML |
| `ML_INTERNAL_TOKEN` | Token compartido de Render y el secreto `historia-viva-ml` en Modal; autoriza `/infer` |

Introducir los valores directamente en GitHub; no guardarlos en archivos ni pegarlos en el chat. Los tokens de API y los del proxy son pares diferentes. La configuración remota del secreto `historia-viva-ml` permanece necesaria. Referencias: [despliegue continuo de Modal](https://modal.com/docs/guide/continuous-deployment) y [autenticación del proxy](https://modal.com/docs/guide/webhook-proxy-auth).

El workflow fija la URL del servicio verificado en esta sesión. Si cambia la cuenta o la aplicación Modal, debe revisarse esa URL antes de desplegar. El identificador se transmite mediante `DEPLOYMENT_SHA` al desplegar y se expone como `deployment_sha`; una ejecución manual sin esa variable informa `unknown` y no satisface la verificación de un SHA concreto.

Estado: implementación y validación locales completas; 51 pruebas ML pasaron al implementar el workflow. El 7 de septiembre de 2026, a las 13:18 UTC, el [despliegue automático de Modal](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34124983079/job/101756701017) terminó correctamente tras configurar los secretos. La verificación informó `passed: true`, BETO listo y SHA servido `6f26e9a91d1d9129666dfdf594aadbc1f543a6cb`, igual al esperado. El resultado quedó archivado como `modal-deployment-34124983079-5`. Esta automatización verifica el servicio ML; el recorrido completo por API y web y la recuperación automática siguen pendientes.

Mantenimiento de Actions registrado en `101e390`: acciones de los cuatro workflows actualizadas a `checkout@v6`, `setup-node@v6`, `setup-python@v6` y `upload-artifact@v6`, que ejecutan internamente Node 24. Validación local con actionlint correcta y ejecución remota de CI, mantenimiento y despliegue Modal comprobada para `328ab3c`. Production smoke también ejecutó las acciones v6; detectó un fallo de salud API/ML descrito al final del documento. Esto atiende el [aviso de retirada de Node 20 en Actions](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/). Un futuro runner propio de BETO deberá tener versión 2.327.1 o superior para estas acciones.

Actualización registrada y publicada en `328ab3c`: ambas etapas del Dockerfile de la API pasaron de `node:20-slim` a `node:22-slim`, alineadas con Node 22 en CI. Node 22 conserva [soporte LTS](https://nodejs.org/en/about/previous-releases); el Node interno de las acciones es independiente de la versión de la aplicación. El 7 de septiembre de 2026 pasaron las 37 pruebas de la API (8 suites) y la compilación con Node 22.23.2 en Windows, usando las dependencias locales existentes. Se utilizó una copia oficial temporal de Node, verificada mediante SHA-256 y guardada en `outputs/`, sin cambiar la instalación del equipo.

Verificación de la publicación del 7 de septiembre de 2026:

- [CI](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34127591506): API, web, ML y Quality gate correctos. Los logs de API confirman Node 22.23.2 y 37 pruebas aprobadas.
- [Mantenimiento ML](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34127591509): experimento completado, evidencias y candidato archivados.
- [Deploy Modal](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34127665129): verificación correcta del SHA `328ab3c688294606a113b67b38e37e5829a70ead`, BETO listo y predicción válida. Durante la transición hubo reintentos por SHA anterior y un error HTTP; la verificación final pasó.
- Render: la autora compartió el evento de Auto-Deploy del commit `328ab3c`, iniciado a las 08:29 de Lima, y luego confirmó que terminó. No se inspeccionaron directamente los logs de construcción ni la versión de Node del contenedor; Docker no está disponible localmente.
- Comprobación posterior a la confirmación de Render, a las 13:33 UTC: seis casos aprobados desde este equipo (salud API/ML, rechazo de credenciales incorrectas, login, acceso a proyectos, abstención sin evidencia y HTML web). El informe local está en `outputs/verification-328ab3c/production-smoke-after-render.json`, excluido de Git. La prueba de salud tardó 0.91 s y la consulta de abstención 31.53 s; esta última sigue siendo lenta. La salud de la API no expone el SHA, por lo que esta comprobación no lo certifica por sí sola.

Primera ejecución remota de [Production smoke](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34128958357), sobre `328ab3c`: falló la comprobación de salud API/ML con `AssertionError` tras 15.15 s; los otros cinco casos pasaron y el informe se archivó. La API limita su consulta de salud a ML a 15 s. Una consulta posterior devolvió `ml: ok`. Esto es compatible con indisponibilidad temporal durante el arranque de Modal, pero no confirma la causa exacta del incidente.

Corrección local del monitor: hasta cuatro intentos de salud con esperas de 10 s, únicamente ante API/ML no listos, errores de red o timeout y HTTP 408/429/500/502/503/504. Se conserva cada intento en el informe y se indica `recovered_after_retry`; los errores de autenticación y las demás comprobaciones no se reintentan. Una indisponibilidad persistente mantiene el resultado fallido. Esto modifica la tolerancia del monitor; no elimina la latencia del servicio.

Verificación local: 55 pruebas aprobadas, incluidas recuperación, indisponibilidad persistente, protección de detalles sensibles y rechazo de autenticación sin reintentos. Las seis comprobaciones contra producción pasaron a las 13:45 UTC, todas en su primer intento; informe local en `outputs/production-smoke-health-retries.json`. La recuperación tras fallos se probó con respuestas simuladas, no se reprodujo un arranque frío real en esta comprobación.

Actualización comprobada el 7 de septiembre de 2026: la corrección se publicó como
`fca473d`; [CI](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34129496981),
[Deploy Modal](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34129561019)
y [Production smoke](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34131192098)
terminaron correctamente. Modal verificó versión y BETO; las seis comprobaciones
de producción pasaron al primer intento. Salud tardó 41.57 s; no demuestra ausencia
de latencia ni valida el recorrido visual PDF. La prioridad solicitada ahora es
el bloque de revisión histórica descrito arriba; la prueba visual sigue pendiente.
