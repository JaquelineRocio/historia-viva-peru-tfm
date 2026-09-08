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
| Palabras frente a caracteres | Comparar dos representaciones en las mismas rondas internas | Caracteres: F1 macro 0.33909 frente a 0.32372; 218 frente a 208 aciertos. Mejora interna modesta que no se mantuvo en validación original |
| Validación de caracteres | Comprobar la variante elegida en los 81 ejemplos originales | F1 macro 0.23521 frente a 0.28987 de palabras; 24 frente a 25 aciertos. Variante descartada para sustituir al TF-IDF de referencia; BETO y producción intactos |
| Preparación de BETO revisado | Verificar recursos y fijar la comparación local | GPU, tokenizador offline, dependencias y artefactos previos comprobados. Receta ganadora conservada y usada en la comparación posterior |
| BETO con datos revisados | Comparar con el checkpoint académico anterior | Entrenamiento local completado: F1 validación 0.43766 → 0.32951; 37 → 33 aciertos de 81. Candidato no seleccionado para sustitución; producción intacta |
| Control de reproducción BETO | Reentrenar los datos originales con la misma receta | Tres épocas con los mismos F1 originales y las 81 predicciones del checkpoint reproducidas; F1 0.43766. Control local completado, sin test ni despliegue |
| Preparación del lote histórico v2 | Recuperar unidades y comprobar su aptitud antes de entrenar | 3 propuestas de reparación, 8 candidatos nuevos condicionados y 1 contexto; ninguna fila incorporada. Medición offline: 443/598 textos de train superan 192 tokens; sin mejora del modelo demostrada |
| Cierre de las reparaciones v2 | Delimitar reemplazos, residuales y dos excepciones de longitud | Propuesta comprobada: 9 filas → 7 unidades; dos excepciones nominales de 109/114 palabras en la guía. Simulación: 596 train con reparaciones, 597 si además se añade Francisca. Ningún dataset modificado |
| Copia experimental del corpus v2 | Aplicar únicamente las reparaciones revisadas | Copia local creada: 596 train, 81 validación y 137 test. Siete textos reemplazados y dos filas retiradas; otras 807 filas intactas. Francisca excluida; sin entrenamiento ni cambios en producción |
| Diversidad de fuentes y reserva de evaluación | Preparar aportes y separar obras relacionadas | Seis unidades propuestas de Contreras/Hünefeldt; un ambiguo, un original conservado y dos textos de Majluf en cuarentena. Dos obras reservadas para evaluación, sin ejemplos extraídos. Dataset intacto; los seis textos propuestos superan 192 tokens |
| Desarrollo externo parcial | Congelar ejemplos y criterios antes de comparar modelos | 31 párrafos: 26 de Sala y 5 de Sobrevilla; cinco categorías. Procedencia, desacuerdos y exclusiones conservados; verificador local y 13 controles de alteración aprobados. Sin entrenamiento ni predicciones |
| Longitud BETO 192 frente a 384 | Aislar max_len con train original y época 2 fija | Comparación local completada: F1 macro externo parcial 0.10000→0.13333; 3→4 aciertos/31. Solo mejora un caso militar; cuatro categorías evaluadas siguen con F1 0. Sin mejora general demostrada ni despliegue |
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

## Generalización entre fuentes de train — registrada en `3c72b21`

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

## Palabras frente a secuencias de caracteres — registrado en `7ef2dcd`

Se amplió [evaluate_tfidf_by_source.py](../scripts/evaluate_tfidf_by_source.py)
con la alternativa `char_wb`: secuencias de 3–5 caracteres dentro de palabras,
con el tratamiento de bordes del analizador. La referencia usa palabras y pares
de palabras. Se conservaron C=4, semilla 42, pesos de clase equilibrados,
`min_df=2`, máximo de 50 000 características y las demás opciones del clasificador
y vectorizador. Se cambió únicamente el analizador y la longitud de sus secuencias.

Las predicciones de palabras se reutilizaron tras comprobar hashes, textos,
particiones y métricas. Solo se entrenaron nueve modelos nuevos de caracteres,
con vocabulario ajustado desde cero en cada ronda. No se cambiaron etiquetas ni
se usaron val/test. La [evidencia comparativa](../artifacts/experiments/character-comparison-v1/report.json)
conserva los resultados y comprobaciones.

| Métrica interna, mismos 598 ejemplos y nueve fuentes | Palabras | Caracteres |
|---|---:|---:|
| F1 macro | 0.32372 | 0.33909 |
| Exactitud | 34.78% | 36.46% |
| Aciertos | 208 | 218 |
| F1 de crisis e ideas | 0.11364 | 0.17204 |
| Aciertos de crisis e ideas | 5/60 | 8/60 |

La exactitud mejora en O'Phelan, Basadre, Orrego y Huamanga; disminuye en Fonseca
y permanece igual en las otras cuatro fuentes. De las predicciones, 48 pasan a
ser correctas y 38 dejan de serlo; 196 cambian de etiqueta en total. Por clase,
el F1 de campañas, liderazgos y organización republicana disminuye, aunque el
promedio global sube. No se ha demostrado significación estadística ni que los
errores de extracción sean la causa del problema.

Verificación: mismas nueve particiones y parámetros del clasificador, modelos
guardados recargados, vocabulario/IDF contrastados con las filas de ajuste,
métricas y diferencias recalculadas. Pasaron 19 rechazos, incluidos una referencia
alterada, otra representación o semilla, cambios de rondas, datos fuera de train
y salidas inválidas. Los nueve ajustes y predicciones tardaron aproximadamente
17.4 segundos sumados; no incluye verificaciones ni importaciones. Los modelos
y predicciones permanecen en `outputs/character-comparison-v1/`, excluidos de Git.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/evaluate_tfidf_by_source.py --dataset outputs/villanueva-snapshot-v1/reviewed-export.json --config configs/experiments/tfidf.json --selection outputs/history-comparison-v1/reviewed/selection.json --previous-report artifacts/experiments/villanueva-comparison-v1/comparison.json --representation char_wb --word-baseline artifacts/experiments/source-generalization-v1/report.json --output outputs/character-comparison-reproduccion
```

Estado: mejora modesta observada **en estas rondas internas**; no es una métrica
de validación original ni de test y no afecta producción. Fue una comparación
de representación prevista, sin nueva búsqueda de parámetros del clasificador.
Siguiente bloque después del commit: ajustar esta variante de caracteres sobre
las 598 filas de train y comprobarla una vez en las 81 de validación original,
comparándola con el resultado registrado de palabras. Mantener test intacto y
decidir según ese resultado, sin desplegar automáticamente el candidato.

## Validación original de la variante de caracteres — registrada en `98351af`

[validate_character_candidate.py](../scripts/validate_character_candidate.py)
verifica la configuración elegida en las rondas internas, el dataset y sus
evidencias. Recarga el TF-IDF de palabras y exige que reproduzca sus predicciones
y métricas anteriores. Después ajusta **un único modelo `char_wb` de 3–5 caracteres,
C=4 y semilla 42** con las 598 filas de train, y predice las 81 de validación.

La [evidencia de validación](../artifacts/experiments/character-validation-v1/report.json)
documenta un resultado negativo para la sustitución:

| Métrica en validación original | Palabras | Caracteres |
|---|---:|---:|
| F1 macro | 0.28987 | 0.23521 |
| Exactitud | 30.86% | 29.63% |
| Aciertos | 25/81 | 24/81 |
| F1 de crisis e ideas | 0 | 0 |
| F1 de campañas | 0.28571 | 0 |

La diferencia de F1 macro es **−0.05466**. Cambian 29 predicciones: ocho pasan a
ser correctas y nueve dejan de serlo; las restantes cambian entre etiquetas
incorrectas. Aunque mejoró el resultado agregado de las rondas internas, esa
ventaja no se mantuvo en esta fuente de validación. No se retocaron parámetros
después de conocer este resultado.

**Decisión: no seleccionar caracteres para sustituir al TF-IDF de palabras.**
Se conserva el candidato y su resultado para trazabilidad. Esta decisión experimental
no equivale a una ejecución del pipeline automático de promoción y no cambia el
BETO que utiliza la aplicación. Validación sigue siendo pequeña, de una fuente
y reutilizada; no representa una evaluación final independiente.

Verificación: ambos modelos recargados reprodujeron las 81 predicciones; métricas
y matrices recalculadas; vocabulario/IDF comprobados contra train y clasificador
con los mismos parámetros. Pasaron 12 rechazos ante datos/candidato/configuración
alterados, referencia incompatible, archivos modificados y salidas inválidas.
El ajuste de caracteres y su predicción tardaron aproximadamente 2 segundos,
sin contar importaciones ni verificaciones. Archivos completos en
`outputs/character-validation-v1/`, excluidos de Git.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/validate_character_candidate.py --dataset outputs/villanueva-snapshot-v1/reviewed-export.json --candidate-evidence artifacts/experiments/character-comparison-v1/report.json --word-report artifacts/experiments/villanueva-comparison-v1/comparison.json --output outputs/character-validation-reproduccion
```

Estado: comparación local completada; no se predijo test, modificó el dataset,
entrenó BETO ni desplegó un modelo. Siguiente bloque después del commit: revisar
la selección previa de BETO, la GPU y dependencias locales, y el flujo de experimentos
para preparar una comparación con configuración fija sobre los datos revisados.
El propósito es volver al clasificador de la aplicación sin seguir ajustando TF-IDF
contra esta misma validación.

## Preparación de la comparación local de BETO — registrada en `2cd193b`

[check_beto_readiness.py](../scripts/check_beto_readiness.py) verifica la receta,
los datos, versiones, caché y checkpoint anterior. Funciona con Hugging Face en
modo offline; no descarga, entrena ni clasifica textos históricos.
La [evidencia de preparación](../artifacts/reviews/beto-readiness-v1.json) conserva
hashes, recursos observados y el protocolo de comparación.

Comprobaciones locales del 7 de septiembre de 2026:

- RTX 3050 Laptop de 4 GB detectada; operación matricial CUDA correcta y unos
  3.2 GB libres en la observación. Esa prueba no garantiza que el entrenamiento quepa.
- PyTorch `2.7.1+cu126`, Transformers `4.57.6`, Tokenizers `0.22.2`, NumPy y
  scikit-learn coinciden con el experimento anterior.
- Revisión BETO `c4d86612f51b4f46759c8390d1798c2febe71b93` disponible en caché,
  incluidos pesos; archivos comprobados por hash. Tokenización local sin conexión correcta.
- Checkpoint seleccionado `beto-lr2e5` presente; metadatos y mapa de etiquetas
  coinciden. Sus predicciones todavía no se reprodujeron en este bloque.
- RAM libre reducida; se registra la medida en la evidencia y deberá revisarse
  antes del ajuste. No se cerraron aplicaciones ni cambiaron dependencias.

La comparación propuesta conserva **lr=0.00002, tres épocas, semilla 42,
microbatch 2, acumulación 8 y longitud máxima 192**, con AdamW, precisión mixta
y gradient checkpointing como antes. La mejor época anterior fue la segunda,
con F1 macro de validación **0.43766**. Se mantienen tres épocas y la selección
de la mejor por validación; reducir a dos cambiaría también el calendario de
aprendizaje. No se repetirá la búsqueda de tres tasas de aprendizaje.

El candidato se ajustará desde la misma revisión BETO base sobre las 598 filas
revisadas, con una cabeza nueva inicializada con la semilla fijada. El checkpoint
afinado anterior servirá para reproducir la referencia en las 81 filas de
validación. No se continuará entrenando ese checkpoint como si fuera el mismo
experimento de comparación entre datasets.

El ejecutor general `run_experiments` **evalúa test automáticamente** después de
seleccionar. Para esta comparación hay que preparar un ejecutor limitado a
validación que llame al ajuste BETO existente con modo offline y guarde evidencia
en una carpeta nueva. No se ejecutó el flujo general ni se consultó test.

Verificación: selección y configuración reproducidas, evaluación congelada idéntica,
artefactos y versiones comprobados. Pasaron 14 rechazos ante cambios de receta,
selección, referencia/evaluación y salidas inválidas. La prueba de GPU y la
tokenización no incluyen carga del modelo ni entrenamiento; el tiempo histórico
de 84.58 segundos no garantiza la duración futura.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/check_beto_readiness.py --output outputs/beto-readiness-reproduccion/report.json
```

Estado: prerrequisitos comprobados y protocolo preparado; sin métricas nuevas,
entrenamiento ni cambios en producción. Siguiente bloque después del commit:
implementar y verificar el ejecutor de comparación solo en validación, y ejecutar
el ajuste local si la comprobación de recursos sigue siendo satisfactoria.

## BETO entrenado con los datos revisados — registrado en `e788d3a`

[compare_beto_validation.py](../scripts/compare_beto_validation.py) implementa
la comparación limitada a validación. Coteja la preparación y los archivos,
comprueba recursos y trabaja offline. Primero recarga el checkpoint académico
anterior y reproduce su F1 de validación 0.43766; si no coincide, detiene el flujo
antes de entrenar. Después llama al ajuste BETO existente solo con train/val.

Se ejecutó **una configuración** desde BETO base con las 598 filas revisadas:
lr=0.00002, semilla 42, tres épocas, microbatch 2, acumulación 8 y longitud 192.
La [evidencia de la ejecución](../artifacts/experiments/beto-reviewed-validation-v1/report.json)
conserva el resultado negativo y la procedencia del candidato.

| Época del nuevo entrenamiento | F1 macro de validación |
|---|---:|
| 1 | 0.29531 |
| 2 | 0.32055 |
| 3, seleccionada | 0.32951 |

| Métrica en los mismos 81 ejemplos | BETO anterior | BETO con datos revisados |
|---|---:|---:|
| F1 macro | 0.43766 | 0.32951 |
| Exactitud | 45.68% | 40.74% |
| Aciertos | 37 | 33 |
| F1 de crisis e ideas | 0 | 0 |

**Decisión: no seleccionar este candidato para sustituir al modelo anterior.**
Seis ejemplos pasan a ser correctos y diez dejan de serlo. Se conservan ambos
artefactos y los datos revisados. La caída no demuestra que las correcciones
históricas sean falsas: cambian conjuntamente textos, etiquetas y orden de filas,
y solo se midió una ejecución con una semilla. La referencia es el checkpoint
académico local; no se cotejaron sus pesos con producción en este bloque.

El ajuste duró 77.33 segundos; la comparación con reproducción de predicciones,
81.37 segundos, sin incluir todas las comprobaciones previas y posteriores.
PyTorch informó un máximo de 2.07 GiB de memoria GPU asignada y 2.26 GiB reservada;
son medidas de ese proceso, no de toda la memoria ocupada por el sistema.
El entrenamiento terminó con los recursos disponibles y sin descargas.

Verificación: el checkpoint guardado reprodujo exactamente sus predicciones de
validación; métricas por clase y matrices recalculadas; hashes y evaluación
congelada intactos. La prueba de orquestación con funciones simuladas comprobó
que test nunca se entrega al entrenador ni al predictor. Pasaron 12 rechazos,
incluidos referencia no reproducible, checkpoint diferente, época/revisión
incorrectas, prerrequisitos alterados y salidas inválidas. No se ejecutó el
pipeline automático de promoción: es evidencia de comparación experimental.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/compare_beto_validation.py --readiness artifacts/reviews/beto-readiness-v1.json --output outputs/beto-reviewed-validation-reproduccion
```

Estado: ejecutor implementado y entrenamiento local completado; modelos,
predicciones y comprobaciones en `outputs/beto-reviewed-validation-v1/`,
excluidos de Git. Sin predicciones de test ni cambios en producción.
Siguiente bloque después del commit: reproducir el entrenamiento de la referencia
original con esta misma receta y entorno, limitado a validación, para comprobar
su reproducibilidad antes de atribuir la caída a los cambios de datos. No iniciar
otra búsqueda de hiperparámetros ni descartar las revisiones históricas por su F1.

## Control de reproducción de BETO — completado localmente, pendiente de Git

Se añadió `--dataset reference` al mismo ejecutor para entrenar exclusivamente
las **596 filas originales**, conservando su orden y toda la receta anterior.
La opción por defecto sigue usando los datos revisados. Ambas opciones cotejan
el dataset correspondiente con su huella registrada antes de entrenar.

El [control local](../artifacts/experiments/beto-reference-control-v1/report.json)
reprodujo los resultados originales:

| Época | F1 original | F1 del control |
|---|---:|---:|
| 1 | 0.32406 | 0.32406 |
| 2, seleccionada | 0.43766 | 0.43766 |
| 3 | 0.31839 | 0.31839 |

Las **81 predicciones de validación coinciden** con las del checkpoint académico:
37 aciertos, mismas métricas por clase y misma matriz de confusión. El candidato
guardado también reprodujo sus propias predicciones al recargarlo. Esto demuestra
reproducción de estos resultados en este equipo; no igualdad de todos los pesos
ni determinismo garantizado en otro entorno.

El BETO revisado sigue por debajo: **0.32951 frente a 0.43766**, con idéntica
receta, versiones de dependencias y evaluación. El control no detectó un fallo
de reproducción que explique esa diferencia. Los cambios de textos, etiquetas,
cantidad y orden de filas se aplicaron juntos: no permite culpar a una corrección
concreta ni invalidar su fundamento histórico. Se conservan ambos datasets y
todos los modelos; no se selecciona el candidato revisado para sustitución.

Verificación: métricas recalculadas desde las predicciones, archivos de entrada
y candidatos cotejados por hash, evaluación congelada intacta y **19 casos de
rechazo aprobados**. Incluyen dataset equivocado, alteración del orden o de
train/val/test, receta diferente y salidas que sobrescribirían archivos. La
prueba con funciones simuladas comprueba que test no llega al ajuste ni a la
predicción; la ejecución real solo utilizó train/val. No se repitió el ajuste
durante la verificación ni se ejecutó el control automático de promoción.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/compare_beto_validation.py --readiness artifacts/reviews/beto-readiness-v1.json --dataset reference --output outputs/beto-reference-control-reproduccion
```

Estado: código implementado y control ejecutado localmente. Pesos, predicciones
y comprobaciones en `outputs/beto-reference-control-v1/`, excluidos de Git.
Sin descargas, uso de Modal, inferencia de test ni cambios en producción.

Siguiente bloque después del commit: consolidar los experimentos y sus límites
en el informe existente de Unidad I, sin seguir ajustando sobre esta misma
validación. Después, retomar las demostraciones funcionales y de mantenimiento
pendientes del plan.

## Mapa curricular e histórico — bloque completado

**Resultado: conservar 1780–1842 y las siete etiquetas; preparar un lote transversal
guiado por cobertura, procedencia y unidades argumentales completas.** No hay
entrenamiento, nuevas etiquetas aplicadas, migración ni cambios en producción en
este bloque. La preparación del lote requiere la confirmación de la autora.
Este bloque, solicitado después del control, pasa a ser la prioridad del plan;
la consolidación del informe y las demostraciones académicas siguen pendientes.

### Evidencia y alcance de la auditoría

Todos los archivos solicitados existen. Se revisaron el informe de Unidad I, la
guía, los dos snapshots, los informes de BETO y generalización, los registros de
revisión y los dos módulos de entrenamiento/comparación. No se encontró un
`AGENTS.md` en el repositorio ni en sus directorios ascendentes consultados.
Git ya mostraba cambios de la autora en este README y en
`scripts/compare_beto_validation.py`, y el directorio del control BETO sin registrar.
Se conservaron. El export de Villanueva está disponible aquí y excluido de Git:
su presencia no garantiza disponibilidad en otro equipo ni despliegue.

Los [recuentos y hashes](../artifacts/reviews/curricular-coverage-v1.json) se
recalcularon sobre todas las filas. La lectura temática abarcó **35 filas de train**:
una por cada combinación existente de fuente y categoría histórica (33), más dos
negativos. Dentro de cada combinación se eligió el primer SHA-256 del texto; los
negativos corresponden a los dos primeros identificadores de fuente ordenados.
Los índices y hashes permiten identificar exactamente la muestra. Las etiquetas
eran visibles: es revisión asistida por IA, no validación humana independiente ni
estimación de la frecuencia de errores. Se aprovecharon también las revisiones
anteriores; no se suman sus muestras como si fueran observaciones independientes.

| Categoría existente | Train congelado | Train revisado | Fuentes en revisado | Concentración comprobada en revisado |
|---|---:|---:|---:|---|
| `contexto_colonial_antecedentes` | 70 | 71 | 4 | Basadre: 52/71 (73.2%) |
| `crisis_ideas_emancipadoras` | 59 | 60 | 5 | O'Phelan y video: 47/60 (78.3%) |
| `participacion_social_regional` | 83 | 83 | 8 | Fonseca y Huamanga: 47/83 (56.6%) |
| `campanias_conflictos_militares` | 89 | 88 | 5 | Basadre: 70/88 (79.5%) |
| `liderazgos_diplomacia_proyectos` | 93 | 94 | 6 | Basadre y O'Phelan: 64/94 (68.1%) |
| `organizacion_consecuencias_republicanas` | 101 | 101 | 5 | Basadre y Orrego: 86/101 (85.1%) |
| `no_relevante` | 101 | 101 | 7 | O'Phelan y video: 56/101 (55.4%) |
| **Total** | **596** | **598** | **9 distintas** | 244/598 filas atribuidas a Basadre (40.8%) |

Se conservan **81 de validación y 137 de test**, idénticas y en el mismo orden
entre versiones. Train revisado contiene 526 filas PDF y 72 de un solo video.
Hay cero coincidencias de `resourceId` y cero textos normalizados idénticos entre
particiones. Esto no descarta reediciones, paráfrasis ni documentos primarios
compartidos. El duplicado de train permanece: índices **709/737** del export
revisado, equivalentes a 718/746 del congelado. No son los índices del diagnóstico
anterior de 600 filas, que no debe reutilizarse como recuento de la versión actual.

**Procedencia y extracción.** Ninguna de las 598 filas lleva página/minuto dentro
del propio registro. Los metadatos adicionales de `added_rows_provenance` permiten
vincular 11 textos por hash con sus localizadores; existen además localizaciones
parciales en revisiones anteriores. No significa que las otras 587 sean imposibles
de rastrear, sino que falta completar esa vinculación. Basadre conserva atribución
del inventario, pero su edición y PDF no se recuperaron; el video carece de audio
y minutos cotejados. O'Phelan, Fonseca, Villanueva, Orrego, Huerta y AGN tienen
PDF locales; no se localizó aquí un PDF de Huamanga en `.corpus-downloads/`.

En el revisado hay **86 PDF con menos de 120 palabras**: 53 negativos y 33
históricos; ninguno supera 250 con el recuento por espacios. Son alertas, no
exclusiones automáticas. La muestra contiene finales cortados (608, 67, 288),
notas mezcladas (161, 278) y biografías sin sujeto explícito (750, 687).
El código de BETO trunca a 192 **tokens**, distintos de palabras: un argumento
completo para el lector puede quedar cortado para el modelo. No se midió aquí la
proporción tokenizada ni se atribuye a esto la caída de F1.

**Resultados existentes.** El control reproduce F1 0.43766 y las 81 predicciones;
el revisado obtiene 0.32951. Ideas permanece en F1 0, pero también hay variaciones
en otras clases: militar 0.75 → 0; liderazgos 0.33333 → 0.57143 (solo cuatro casos
de validación en cada una). Nueve de los 15 casos de ideas se confundían con
organización en la referencia. La validación contiene únicamente el artículo de
Guarisco y ya se reutilizó. La evaluación interna TF-IDF dejando fuera fuentes
obtuvo 0.32372; los caracteres mejoraron ese diagnóstico a 0.33909, pero empeoraron
la validación a 0.23521 frente a 0.28987. Ninguno de esos resultados demuestra
mejora de BETO ni aísla una causa: variaron textos, etiquetas, cantidad y orden.

### Fundamento curricular y público todavía provisional

**Oficial.** Se consultó el [Programa curricular de Educación Secundaria del
MINEDU](https://www.minedu.gob.pe/curriculo/pdf/programa-curricular-educacion-secundaria.pdf),
documento con RM 649-2016-MINEDU, pp. **45 y 48**, cotejadas visualmente en el PDF
oficial descargado. La competencia es «Construye interpretaciones históricas»:
interpretar críticamente fuentes diversas, comprender el tiempo histórico y
elaborar explicaciones sobre procesos históricos. En tercero se trabaja desde
la organización virreinal hasta el surgimiento republicano; se comparan fuentes,
causas, consecuencias, simultaneidades, cambios y permanencias. En cuarto aparece
el primer militarismo. El MINEDU no impone nuestras seis categorías ni el corte
exacto de 1842. No se confunde este documento con la versión preliminar de junio
de 2016, también accesible en su web, cuya redacción es diferente.

**Interpretación curricular.** Tercero es una hipótesis bien sustentada para el
núcleo de independencia, con mediación docente. La formación republicana hasta
1842 puede funcionar como articulación con cuarto; no se presenta todo el alcance
como contenido exclusivo de tercero. Falta confirmar con la autora el grado,
el contexto de uso y la dificultad de lectura antes de adaptar definitivamente
la aplicación. Esto no condiciona la auditoría histórica del corpus.

**Propuesta propia.** Para cada eje, ofrecer un fragmento con autor, fecha y
localizador, una fuente de contraste y una pregunta que exija explicar una
relación histórica. Evaluar si el estudiante cita evidencia, sitúa el proceso y
justifica una causa o permanencia. Clasificar correctamente un texto no demuestra
aprendizaje. Estas actividades son diseños del proyecto, no desempeños copiados
del MINEDU ni funcionalidades nuevas ya implementadas.

### Mapa de los seis ejes

Las presencias siguientes están comprobadas **en muestras**, con índices del
export revisado (base cero). Describen contenido, sin aprobar automáticamente su
etiqueta. Las necesidades son insuficiencias de evidencia utilizable o diversidad;
no se declara ausente un asunto por no encontrar una palabra.

| Eje | Propósito educativo y pregunta histórica propia | Representado en train observado | Insuficiente o pendiente de comprobar | Ejemplos y fuentes prioritarios |
|---|---|---|---|---|
| Antecedentes coloniales | Explicar condiciones y distinguirlas de detonantes: ¿por qué las cargas y jerarquías generaban respuestas distintas? | Reformas y acceso a cargos (608); circuitos textiles de Huamanga, 1780–1830 (67); esclavización y venta de 1805, AGN01 (805). | Diversidad escasa fuera de Basadre; argumentos fiscales cortados. Cobertura sistemática de tributo, mita, mercados y diferencias sociales todavía sin inventario por pasaje. No confundir contexto regional con fronteras nacionales actuales. | Recuperar unidad fiscal de O'Phelan y unidad económica de Huamanga; AGN01 ya está incorporado y sirve de contraste, no de nueva fila. Excluir del lote los tramos de O'Phelan anteriores a 1780 que no constituyan contexto necesario del proceso delimitado. |
| Crisis e ideas | Comparar legitimidades: ¿cómo se justificó obedecer al rey, reformar la monarquía o romper con ella? | Manifiestos y despotismo (185); lectura de literatura política, HUE03 (810); argumentación sobre libertad y orden (751). | No está acreditada una secuencia completa y bien localizada de crisis de 1808, soberanía, Cádiz y censura; 47/60 dependen de dos fuentes. El video mezcla historiografía posterior (385). | Contrastar HUE01–04 existentes con Martínez Riaza o Hampe sobre imprenta/Cádiz; localizar un argumento de soberanía de 1808–1814. No duplicar HUE03/HUE04 ni forzar como ideas toda mención de Constitución. |
| Participación social y regional | Explicar decisiones de actores: ¿por qué comunidades próximas apoyaron bandos distintos y qué intentaban conseguir? | Alianzas de caciques (591); divergencia Huanta/Huamanga (348); reclutamiento indígena y afrodescendiente (765); cofradía de negros libres en 1834, AGN02 (806); tierras comunales (36). | Ocho fuentes no prueban amplitud territorial. No se cuantificó cobertura del norte, Amazonía, mujeres ni agencia afrodescendiente; AGN aporta un solo caso social. Hay opiniones historiográficas, no testimonios directos, en 46/679. | Recuperar motivaciones regionales en Huamanga/Fonseca; contrastar agencia y coerción. Examinar Arguedas Pinasco sobre mujeres/rabonas, conservando la perspectiva mediada por Flora Tristán. AGN02 conserva fecha en contexto y no se duplica. |
| Campañas y conflictos | Relacionar espacio, recursos y resultados: ¿cómo condicionaron abastecimiento, terreno y guerrillas el curso de la guerra? | Maniobra y munición de 1829 (549); confiscaciones, deserciones y represión de 1814–1815 (324); estrategia guerrillera junto con discusión de fuentes (161). | 79.5% depende de Basadre. Falta comprobar equilibrio entre guerras de independencia y conflictos republicanos; los recuentos por etiqueta no dicen cuántos ejemplos completos hay de Junín, Ayacucho, campañas del sur o del norte. | Fonseca pp. 117–118 para estrategia y unidades completas; localizar abastecimiento o financiamiento en fuente distinta de Basadre. No añadir relatos redundantes de batallas ni etiquetar militar una reflexión general sobre violencia (699) sin contexto. |
| Liderazgos, diplomacia y proyectos | Comparar alternativas y restricciones: ¿qué Estado se propuso y cómo se buscó hacerlo viable? | Crítica bolivariana al diseño constitucional (645); organización atribuida a Otero (63); alianzas políticas en transcripción (683); caudillismo (626); reparación V04 de Villanueva ya incorporada. | Algunas unidades mezclan actuación personal, instituciones y grupos. Falta localizar contrastes completos entre monarquía, república y proyectos de unión/confederación; escasez documental diplomática no cuantificada. | Villanueva p. 428 como referencia ya revisada; una misión de reconocimiento o negociación en la colección oficial Misiones peruanas, una vez verificada edición/página/reutilización. No convertir la mera presencia de San Martín o Bolívar en criterio. |
| Organización y consecuencias republicanas | Contrastar norma y experiencia: ¿qué cambió con la República y qué relaciones persistieron? | Elección presidencial y predominio del Congreso (7); mercado regional y continuidad social (199); militarismo y fragmentación (288); organización/ciudadanía en V03/V06/V07 existentes. | 85.1% proviene de Basadre/Orrego. Hay recortes que alcanzan 1845 o cincuenta años republicanos (288/469), sin tramo autónomo de 1780–1842 delimitado. La economía sí está representada, pero falta continuidad y cobertura comprobada por subtema. | Recuperar Orrego pp. 191–192 sobre minería y agricultura hasta 1840; contrastar ciudadanía constitucional con condiciones sociales. Constitución de 1823, arts. 17 y 22–23, como pista para cotejar norma, vigencia y práctica. |

No se crean subetiquetas para economía, género, región o tiempo. Pueden
registrarse como dimensiones descriptivas de la revisión, sin cambiar el esquema
del dataset. Un mismo hecho puede dar lugar a unidades diferentes según la
pregunta dominante; no a copias del mismo texto con etiquetas contrapuestas.

### Fronteras operativas propuestas, sin modificar la guía ni adjudicar filas

Los siguientes son **ejemplos didácticos de criterios**, no citas recuperadas ni
texto apto para entrenamiento. La decisión final exige el pasaje y su contexto.

| Frontera | Ejemplo de criterio positivo | Contraejemplo / otra categoría |
|---|---|---|
| Colonial ↔ ideas | Describir cómo se cobra el tributo y quién soporta la carga: colonial. | Argumentar quién tiene soberanía tras la crisis monárquica: ideas; la fecha temprana no basta para colonial. |
| Ideas ↔ proyectos | Defender legitimidad, derechos o libertad de imprenta: ideas. | Diseñar o negociar una monarquía, república o unión concreta: proyectos. Un liberalismo mencionado al describir órganos ya establecidos puede ser organización. |
| Social ↔ militar | Explicar por qué una comunidad negocia apoyo o resiste una leva: social. | Describir posición, maniobra, abastecimiento o resultado bélico: militar, aunque participen indígenas o mujeres. |
| Militar ↔ diplomacia | Relatar operaciones y términos operativos de rendición: militar. | Negociar reconocimiento, paz, indemnizaciones o alianzas: diplomacia, aunque ocurra durante una guerra. |
| Proyectos ↔ organización | Defender una alternativa futura de gobierno: proyectos. | Explicar competencias constitucionales, aplicación de leyes o funcionamiento fiscal: organización. Un proyecto fallido no equivale a una institución vigente. |
| Social ↔ organización | Reconstruir acciones e intereses de cofradías/comunidades: social. | Explicar reglas generales de ciudadanía, propiedad o contribución y sus consecuencias: organización. |
| Histórico ↔ no relevante | Bibliografía aislada, moderación del evento o discusión contemporánea sin argumento histórico del periodo: negativo. | Una nota con evidencia sustantiva o interpretación posterior sobre 1780–1842 no es negativa automáticamente. Distinguir fecha del hecho y fecha de publicación. |

Para unidades mixtas: recuperar primero la página anterior/siguiente o audio,
resumir la tesis en una frase de revisión y decidir por su función explicativa.
Si pueden separarse dos argumentos completos, proponer resegmentación conservando
original y relación; si no, mantener el caso **ambiguo fuera del lote candidato**.
`ambiguo` es estado de revisión, no una octava etiqueta. No usar la predicción
ni el F1 para resolver la interpretación. Los casos 768 (ideas en colonial),
626 (caudillismo entre proyectos e instituciones), 161 (estrategia e historiografía)
y 288/469 (alcance temporal) quedan como señales, no correcciones aprobadas.

### Fuentes con prioridad y condiciones de uso

Se priorizan las descargas existentes. Acceso público no se interpreta como
licencia abierta. Los localizadores siguientes identifican zonas para recuperar
o contrastar; no certifican candidatos inéditos ni independientes de evaluación.

| Fuente y procedencia | Localizador / aportación | Reutilización y estado |
|---|---|---|
| Scarlett O'Phelan, 1985, Histórica 9(2), 155–191, [ficha editorial](https://revistas.pucp.edu.pe/index.php/historica/article/view/8222) | pp. 188–189, PDF 34–35: fiscalidad y programas; recuperar contexto al principio/final. | CC BY 4.0 visible. PDF local; ya es fuente train. Solo pasajes necesarios y no duplicados; distinguir interpretación de autora y documentos citados. |
| Juan Fonseca Ariza, 2010, Histórica 34(1), 105–128, [ficha editorial](https://revistas.pucp.edu.pe/index.php/historica/article/view/95) | pp. 115–118: participación, guerrillas y estrategia; pp. 108–109 ya reparadas. | CC BY 4.0 visible. PDF local, train; la CDIP citada impide tratar cada cita como fuente independiente. |
| María Claudia Huerta Vera, 2020, Histórica 44(1), 125–158, [ficha editorial](https://revistas.pucp.edu.pe/index.php/historica/article/view/23275) | pp. 138, 140–141 y 145: HUE02/03/04/01 existentes. | CC BY 4.0 visible. Reutilizar como referencia, sin volver a añadir. Lectura política y propaganda no prueban recepción idéntica entre todos los sectores. |
| Juan José Brito Ramos, 2017, Revista del AGN 32(1), 15–45, [ficha editorial](https://revista.agn.gob.pe/ojs/index.php/ragn/article/view/5) | pp. 21 y 35: AGN01/02 existentes, colonial y social. | CC BY 4.0 visible. PDF local. AGN03 es contexto relacionado; los episodios tardíos y el error cronológico identificado en p. 17 siguen apartados. |
| Carmen Villanueva, 1996, BIRA 23, 427–435, PDF local `.corpus-downloads/constitucion_1823.pdf` | pp. 428 y 430–431: proyectos y organización; V04/V06/V07 ya incorporados. | Metadatos de reparación cotejados; licencia no verificada nuevamente. Este archivo es el artículo de Villanueva, **no** el facsímil de la Constitución. Evitar nuevas sustituciones redundantes. |
| Juan Luis Orrego Penagos, BIRA 15, 179–197, [repositorio PUCP](https://repositorio.pucp.edu.pe/items/3344e6fb-39b9-4266-aabc-7900373c1126) | pp. 185–187 y 191–192, PDF local 7–9 y 13–14: militarismo, sectores populares, minería y agricultura. | PDF local consultado; edición marcada 1988, con nota que remite a una memoria prevista para 1989. Ficha completa/licencia pendientes de cotejo; reparar antes que acumular más Orrego. |
| Ascensión Martínez Riaza, Libertad de imprenta y periodismo político en el Perú, 1811–1824, [metadatos PUCP](https://repositorio.pucp.edu.pe/items/4886bb23-1e37-4584-a5bb-9b964137e6ee/full) | Cádiz, imprenta y debate; página de los candidatos pendiente. | La ficha registra 2010, Summa Humanitatis 4(2), y CC BY 4.0. Referencias académicas identifican un texto homónimo de 1984: cotejar edición antes de asignar autoría/fecha al extracto y agrupar ambas versiones. Huerta la cita; no asumir independencia documental. |
| María José Arguedas Pinasco, 2022, Conexión 17, 85–105, [ficha editorial](https://revistas.pucp.edu.pe/index.php/conexion/article/view/26124) | Mujeres y rabonas a través de Flora Tristán; página exacta y contexto del pasaje pendientes. | CC BY 4.0 visible; publicación 28-07-2022 y aviso de copyright 2024 en ficha, conservar distinción. El resumen sitúa el viaje en 1832–1833: cotejar cronología con la edición de Tristán antes de usarla. No se extrajeron citas para train. |
| Primer Congreso Constituyente, Constitución de 1823, [transcripción del Congreso](https://www3.congreso.gob.pe/Docs/sites/webs/quipu/constitu/1823.htm) | Arts. 17, 22–23 y 27–29; ciudadanías y reglas institucionales. | Texto oficial consultable; licencia de la edición digital sin comprobar. Falta facsímil y hay anomalía de numeración ya registrada. El art. 11 figura en train; rastrear otras citas compartidas. |
| Misiones peruanas 1820–1826, vol. 1, [repositorio oficial Bicentenario](https://repositorio.bicentenario.gob.pe/handle/20.500.12934/148?show=full) | Reconocimiento, apoyo económico y alianzas; elegir documento con remitente, destinatario y fecha dentro del periodo. | Pista del catálogo/indexación; acceso directo falló en esta sesión. Compilador, fecha de edición, páginas y licencia pendientes: **no listo para extracción**. Comprobar relación con CDIP, Basadre y otras citas antes de seleccionarlo. |

La Abeja Republicana de BNP sigue pospuesta por OCR, fecha/número y condiciones
de la edición no resueltos. Hampe (2012), [La primavera de Cádiz](https://www.historiaconstitucional.com/index.php/historiaconstitucional/article/view/336),
es respaldo bibliográfico alternativo para ideas; falta comprobar licencia y
página antes de seleccionar un pasaje. No ampliar búsquedas indefinidamente si
Martínez Riaza proporciona las unidades necesarias.

**Separación documental obligatoria.** El inventario local vincula validación con
Guarisco, José de San Martín y el espacio político indígena (2023), y test con el
artículo sobre la celebración en Santiago de Chile y el video de la rebelión de
Huánuco. No proponer textos, otras ediciones ni citas derivadas de esas obras
para train. El control por `resourceId` es insuficiente: comparar también título,
autor, edición, DOI y documento primario. De evaluación solo se usan identidades
y controles mecánicos de integridad/solapamiento, no contenido para elegir el lote.

### Propuesta del lote — preparación confirmada y resultado registrado abajo

El siguiente bloque debe **preparar candidatos y decisiones**, todavía sin
entrenar. El lote se organiza por estas doce necesidades; son objetivos de
selección propios, **no doce ausencias demostradas ni una cuota de doce filas**.
Primero comprobar qué unidades existentes ya los cumplen. Cada objetivo termina
como cubierto, reparable, candidato nuevo o pendiente, con evidencia y motivo.

| Prioridad | Necesidades que deben quedar resueltas | Acción limitada |
|---|---|---|
| 1. Integridad antes de añadir | **A1** fiscalidad/reformas; **A2** relaciones coloniales de trabajo y esclavitud; **F2** economía republicana | Recuperar contexto de 608/67; aprovechar AGN01; delimitar economía de Orrego pp. 191–192 y comprobar solapamientos. Revisar 709/737 como duplicado propuesto, sin borrarlo automáticamente. |
| 2. Contrastes explicativos | **B1** crisis y soberanía; **B2** circulación/censura; **E1** alternativas de gobierno; **F1** ciudadanía e instituciones | Usar Huerta y Villanueva existentes como contraste. Examinar una fuente adicional de ideas y la Constitución cotejada. No volver a añadir los mismos HUE/VIL. |
| 3. Actores y guerra | **C1** decisiones de comunidades y grupos afrodescendientes; **C2** acciones de mujeres; **D1** logística/recursos; **D2** estrategia guerrillera | Reutilizar Huamanga/Fonseca y AGN02; revisar Arguedas Pinasco como nueva perspectiva; buscar para D1 una unidad documental que reduzca dependencia de Basadre. Un pasaje de rabonas no satisface automáticamente C2 y D1 con dos copias. |
| 4. Dependiente de acceso | **E2** negociación diplomática y reconocimiento | Abrir y verificar un documento de Misiones peruanas. Si no hay acceso o derechos claros, registrar pendiente y no reemplazarlo con texto generado. |

La cantidad final será el saldo de unidades completas aprobadas, reemplazos y
duplicados identificados, no el mínimo de 20 cambios que activa mantenimiento ni
una meta de equilibrio artificial. Antes de incorporarlas, presentar el manifiesto
con originales, página impresa/PDF o minutos, fecha del hecho/publicación, autoría,
enlace, licencia, hash, cambios de extracción, clase propuesta y alternativa,
relaciones documentales y decisiones ambiguas. Conservar todas las versiones.
Ningún candidato aprobado debe carecer de localizador o condición de uso resuelta.

**Comprobación de calidad del lote:** informar necesidades cubiertas de las 12,
unidades nuevas/reparadas/pendientes por eje, fuentes y documentos primarios
distintos, porcentaje con trazabilidad completa, concentración por fuente y
alertas de extracción resueltas. Examinar semejanza exacta y secuencias de cinco
palabras con los umbrales existentes (Jaccard ≥0.25 o contención ≥0.8), además de
dependencia bibliográfica; los umbrales solo señalan revisión. Un desacuerdo entre
dos agentes sigue siendo revisión IA, no validación humana. No se pide a la autora
resolver disputas históricas: se busca evidencia o se conserva la ambigüedad.

**Hipótesis para una comparación posterior, no autorizada por este bloque:** las
unidades íntegras, los contrastes claros y la diversidad documental pueden mejorar
la clasificación y la recuperación de evidencia. Separar reparación de extracción
y ampliación de cobertura en manifiestos, conservando orden de las filas no
afectadas; no cambiar a la vez hiperparámetros ni arquitectura. Medir primero
truncamiento real a 192 tokens sin entrenar. Si hay que modificar la longitud,
formular otra hipótesis: no mezclarla silenciosamente con el cambio de datos.

Antes de experimentar, congelar una evaluación nueva por **obras y documentos
relacionados**, con fuentes distintas de las usadas para construir el lote,
cobertura de las siete clases y varios contextos documentales por clase. Definir
por separado conjunto de desarrollo y prueba final, protocolo de revisión y
tamaño según los materiales disponibles; el diseño no está todavía congelado.
Los textos reservados no se reutilizan como entrenamiento. Comparar referencia y
candidato con la misma receta y partición; medir F1 macro, F1/soporte por clase,
confusiones y resultados por fuente. Solo considerar mejora si supera la referencia
en el criterio predeclarado, sin convertir una clase en inoperante, y exponer la
incertidumbre por fuente. Un incremento aislado en la validación antigua no basta.
No usar test para decidir datos o hiperparámetros ni sustituir producción con un
candidato inferior; cualquier entrenamiento remoto o despliegue requiere permiso.

**Utilidad educativa propuesta:** preparar seis pares de fuentes, uno por eje,
con las preguntas del mapa y criterios observables de respuesta (evidencia,
tiempo, explicación). Esos pares sirven para revisar el material con mediación
docente; no constituyen seis nuevas pruebas aprobadas ni una métrica de aprendizaje.
Las entregas siguen siendo: Unidad I con funcionamiento en inglés, dataset,
entrenamiento, características, optimización, métricas, despliegue y dos pruebas;
Unidad II con producto, mantenimiento/CI y tres casos ejecutados de esos procesos.
El mapa contribuye a su fundamento y no sustituye las demostraciones pendientes.

Estado del bloque: propuesta documentada y auditoría local; ninguna nueva
verificación en producción. Se conservan los datasets, etiquetas y código.
Comprobaciones de cierre: hashes de entradas, recuentos, muestra, igualdad de
evaluación y taxonomía, conservación de cambios previos y `git diff --check`.
PDF oficial, imágenes de cotejo y auxiliar de cálculo quedan solo en
`outputs/curricular-coverage-v1/`, excluido de Git. Siguiente paso: confirmar la
preparación del lote descrito; el grado definitivo puede decidirse antes de la
adaptación del producto, sin bloquear esa preparación histórica.

## Preparación del lote histórico v2 — bloque cerrado

La autora confirmó preparar el lote. Resultado local del 7 de septiembre de
2026: **3 propuestas de reparación, 8 candidatos de obras nuevas condicionados
y 1 párrafo de contexto**. No hay filas incorporadas ni mejora del modelo
demostrada. El [manifiesto](../artifacts/reviews/corpus-batch-v2.json) conserva
localizadores, hashes, propuestas de categoría, revisiones y condiciones.
Las transcripciones y originales están en `outputs/corpus-batch-v2/`.

| Unidades recuperadas | Páginas impresas; palabras | Resultado y condición pendiente |
|---|---|---|
| OPH-A1, reformas y cargos | O'Phelan, 183–184; 212 | Colonial. Reparación cotejada; revisar juntas 598/608 para no duplicar el cierre ni perder los demás párrafos de 598. Oruro de 1780 se conserva como comparación andina. |
| FON-D1, convocatoria y autosostenimiento | Fonseca, 117–118; 246 | Militar. Dos apartados completos de una enumeración que continúa. Revisar 78/149/157 y conservar el contenido restante. Mantener las conjeturas atribuidas al autor. El cierre posterior verificó seis apartados al consultar p. 119. |
| ORR-F2 y su contexto | Orrego, 191–192; 218 + 109 | Republicana. Las regiones agrícolas dependen del párrafo previo para fijar el periodo hasta 1840; BETO no recibe ese contexto. 109 palabras quedan como contexto, sin rellenar. Revisar 19/24/25. |
| MR1984-P151-A y P157-A | Martínez Riaza, 151 y 157; 183 y 149 | Ideas: prensa y censura, no crisis de soberanía de 1808. La edición textual es 1984; dos registros oficiales discrepan en año/licencia. No incorporar hasta aclararlo. |
| Rabonas 01 y 02 | Arguedas, 100–101; 233 y 166 | Militar y social respectivamente, por el argumento dominante. Citan traducción de Tristán de 2003 cuyos derechos no quedaron acreditados. No confundir licencia del artículo con la de la traducción. |
| Francisca, prosa de Arguedas | Arguedas, 97; 114 | Social, con alternativa liderazgo. Párrafo completo de la autora, pero inferior a las 120 palabras de la guía; cualquier excepción requiere decisión explícita. No se añadió relleno. |
| diplomacy-01 y 02 | Misiones peruanas, 431 y 218; 174 y 228 | Diplomacia: expectativa de reconocimiento y negativa a un empréstito. El reconocimiento todavía es esperado en la carta; las finanzas son el argumento de la parte chilena. |
| diplomacy-03 | Misiones peruanas, 258; 223 | Militar: amenaza naval, escolta y aplazamiento de refuerzos. El formato de carta diplomática no determina la categoría. |

Las tres cartas corresponden al 25-05-1822, 22-01-1824 y 28-08-1824, en la
compilación de Carlos Ortiz de Zevallos Paz-Soldán (1975). Se cotejaron imágenes
del visor de la BNP. El [catálogo oficial de Misiones peruanas](https://repositorio.bicentenario.gob.pe/handle/20.500.12934/148?show=full)
indexado declara CC BY-NC-SA 4.0, pero su consulta directa falló: queda
condicionada la incorporación, sin afirmar que el catálogo actual se descargó.

Las fichas editoriales de [O'Phelan](https://revistas.pucp.edu.pe/index.php/historica/article/view/8222)
y [Fonseca](https://revistas.pucp.edu.pe/index.php/historica/article/view/95)
declaran CC BY 4.0. El registro de [Orrego](https://repositorio.pucp.edu.pe/items/3344e6fb-39b9-4266-aabc-7900373c1126)
enlaza esa licencia, aunque su rótulo visible dice acceso abierto; un intento
posterior de lectura agotó el tiempo. Para Martínez Riaza se conservaron los
metadatos de ambos registros: [1984, CC BY-NC-ND 2.5 PE](https://repositorio.pucp.edu.pe/items/89ad9193-bee7-45cf-8174-8f410cdf9c3f)
y [2010, CC BY 4.0](https://repositorio.pucp.edu.pe/items/4886bb23-1e37-4584-a5bb-9b964137e6ee/full).
El [artículo de Arguedas](https://revistas.pucp.edu.pe/index.php/conexion/article/view/26124)
declara CC BY 4.0; se conservaron sus discrepancias cronológicas y se apartaron
los párrafos con erratas. No se corrigieron afirmaciones históricas para hacerlas
encajar en el periodo. Las voces de autora, viajera y corresponsales permanecen
atribuidas; no se autenticaron manuscritos ni la traducción original.

**Saldo de las doce necesidades, sin declarar cobertura exhaustiva.** A1 y D1
tienen reparaciones propuestas; F2 necesita resolver el contexto temporal.
B2, C2 y E2 tienen candidatos condicionados. A2 y C1 ya cuentan con AGN01/02,
pero las unidades de Huamanga 67/348 siguen cortadas y su PDF no está localmente.
E1/F1 conservan V04 y V03/V06/V07 ya incorporados; no se duplican. B1 continúa
pendiente; D2 tiene material en 157/161, aún sin unidad completa revisada de
estrategia guerrillera. Diez unidades previas AGN/HUE/VIL fueron identificadas
en el export actual; ocho mediante cotejo de hashes con sus revisiones previas.
La Constitución original de 1823 sigue pendiente de cotejo. No se cambia el
mapa MINEDU ni se confirma todavía el grado definitivo del producto.

**Medición que orienta el siguiente experimento.** El tokenizador local de BETO,
sin cargar pesos ni hacer inferencia, produjo estos recuentos de train, incluidos
los tokens especiales:

| Dataset | Filas | Superan 192 tokens | Superan 256 | Superan 384 |
|---|---:|---:|---:|---:|
| Referencia congelada | 596 | 442 (74.2%) | 272 | 4 |
| Copia revisada | 598 | 443 (74.1%) | 269 | 4 |

Diez de las doce unidades preparadas también superan 192 tokens. El recorte es
común a ambas versiones: **no demuestra la causa de la caída de F1** ni que todos
los finales contengan información decisiva. Mantenerlo como hipótesis separada:
comparar, si se autoriza posteriormente, 192 frente a 384 con los mismos datos,
orden y parámetros restantes. Puede aumentar memoria y tiempo; todavía no se ha
medido ese coste ni se promete mejora. No combinarlo con un cambio del corpus.

**Controles locales.** Doce unidades cotejadas visualmente y revisadas dos veces
con la primera etiqueta oculta; las doce propuestas principales coinciden. Son
juicios de IA que comparten contexto, no validación humana ni una métrica del
modelo. Los ocho candidatos nuevos no activan alertas léxicas con train; ninguna
de las doce unidades las activa con validación/test ni entre sí. Los umbrales
son los del mapa. Esto no certifica independencia bibliográfica: se conservaron
relaciones Huerta/Martínez, Arguedas/Tristán/Iribarne y CDIP/Fonseca/Basadre.
Se archivaron ocho filas originales relacionadas con las reparaciones. El
duplicado 709/737 sigue identificado y sin retirar. Los datasets, su evaluación,
las etiquetas y los dos archivos de código comprobados mantienen sus hashes.

Incidente registrado: un agente mostró accidentalmente una fila de validación
al inspeccionar la estructura del export. No la usó para seleccionar o etiquetar
candidatos ni la copió a los artefactos. No se afirma que ningún revisor viera
validación. Los controles posteriores procesaron evaluación solo mecánicamente,
sin mostrar sus textos o usar sus resultados para ajustar la propuesta.

Para el cotejo visual se instaló PyMuPDF 1.26.7 únicamente en
`outputs/corpus-batch-v2/pdf-renderer`, sin modificar dependencias del proyecto.
PDFs, imágenes y auxiliares quedan fuera de Git y pueden faltar en otro equipo.
No hubo entrenamiento, métricas nuevas, llamadas a Modal ni cambios o nuevas
comprobaciones en producción. Las obligaciones de ambas unidades académicas
permanecen como figuran en el plan.

**Continuación confirmada, resultado registrado a continuación:** cerrar la
resegmentación de los tres grupos y decidir una excepción documentada para los
dos párrafos completos de 109/114 palabras; no ampliar búsquedas a otras obras.
Los candidatos con derechos sin resolver permanecen fuera del corpus aplicable.
Antes de entrenar se necesita fijar la evaluación separada por obras/documentos
ya propuesta y elegir una sola hipótesis. Una mejora solo en la validación
antigua, de una fuente y reutilizada, no acreditaría generalización.

## Reemplazos y excepciones v2 — propuesta cerrada

La propuesta concreta está en [corpus-closure-v2.json](../artifacts/reviews/corpus-closure-v2.json).
**Se cerraron los tres grupos y se documentaron las dos excepciones; no se aplicó
la propuesta al dataset ni se entrenó.** Los índices siguientes pertenecen al
export revisado actual y empiezan en cero. Los hashes impiden aplicarlos por
posición a otro export diferente.

| Grupo | Reemplazo propuesto | Contenido y efecto |
|---|---|---|
| O'Phelan | 598 → OPH-R1 (157 palabras); 608 → OPH-A1 (212) | Dos filas por dos. Se recompone el cierre fiscal y se conserva el resto sobre aduanas y respuesta de Túpac Amaru; mismas etiquetas y posiciones. |
| Orrego | 19 → párrafo causal (109); 24 → regiones (218); retirar 25 | Tres filas por dos. Conserva causas económicas y geografía; recortes minero/estadístico quedan como contexto. La fecha del pasaje regional sigue dependiendo del párrafo anterior. |
| Fonseca | 78 → convocatoria/recursos (246); 157 → jerarquías/coordinación (169); 162 → espionaje/trato civil (125); retirar 149 | Cuatro filas por tres. El cierre ya estaba en 162: incluirla evita duplicarlo. El subpunto de 1825–1828 queda como contexto. |

La primera propuesta de Orrego retiraba también la geografía de 218 palabras.
La revisión separada objetó esa pérdida: la dependencia temporal del contexto
no demuestra inutilidad para BETO y la guía permite consultar contexto. Se
aceptó la objeción y se conservaron ambas alternativas y sus motivos. No se
añadió una fecha sintética al texto para resolver la limitación del modelo.

El cotejo de Fonseca p. 119 corrigió la descripción anterior: la enumeración
tiene **seis apartados**, no cuatro. La unidad de 125 palabras conserva la
reserva sobre incumplimiento de las recomendaciones de buen trato; su apartado
final continúa con una oración de 13 palabras, archivada como contexto. Tampoco
OPH-R1 contiene íntegro su segundo párrafo: selecciona dos oraciones completas y
conserva el resto como contexto. No se declara cubierta toda la estrategia D2.

La [guía](../docs/guia-etiquetado-1780-1842.md) incorpora excepciones de longitud
solo para los hashes de **ORR-F2-context (109)** y
**arguedas-francisca-author-01 (114)**: párrafos íntegros, autónomos, con periodo,
argumento y atribución. No se añadió relleno ni se redujo el mínimo general.
Orrego pasa de contexto a candidato en la propuesta; Francisca queda como
**alta separada**, para no mezclar reparación y nueva fuente en un experimento.
Las etiquetas existentes no cambian; se sostienen por la revisión temática.

**Coste de cobertura declarado antes de aplicar:** 43 palabras brutas de créditos
mineros y 57 de estadísticas en Orrego, más 44 del subpunto de Fonseca sobre
1825–1828, quedan fuera de estas filas propuestas de entrenamiento. Las 144
palabras y los originales completos se conservan; no se marcan `no_relevante`.
Este recuento no significa que esos temas desaparezcan del conjunto completo.

**Comprobación local:** 75 particiones reconstruyen todos los caracteres de
nueve originales. Se recompusieron seis límites entre filas y la simulación
conserva las otras 807 filas, su orden relativo y las 81/137 de evaluación.
Las ocho unidades, incluida el alta separada, no activan alertas de duplicación
exacta/contención ni los umbrales de cinco palabras frente a las 589 filas train
restantes, validación/test o entre sí. Se conserva la cautela sobre dependencias
documentales y el incidente de validación del bloque anterior; en este bloque
la evaluación solo se procesó mecánicamente, sin mostrar textos ni etiquetas.

| Escenario simulado; ninguno aplicado | Train | Fuentes de train | Validación / test |
|---|---:|---:|---:|
| Export revisado actual | 598 | 9 | 81 / 137 |
| Solo las reparaciones propuestas | 596 | 9 | 81 / 137 |
| Reparaciones y alta separada de Francisca | 597 | 10 | 81 / 137 |

Las revisiones son asistidas por IA y no ciegas en este cierre; no son validación
humana. Cinco de las siete unidades reparadas aún superan 192 tokens. No cambió
`max_len`, no hay nuevas métricas y ninguna mejora de BETO está demostrada por
esta simulación. Los siete candidatos con derechos pendientes del lote anterior
siguen excluidos; el duplicado previo 709/737 permanece sin retirar.

Fuentes, imágenes y auxiliares existentes se reutilizaron; no se instalaron
dependencias ni se abrieron nuevas obras. Evidencia local en
`outputs/corpus-closure-v2/`, excluida de Git. Datasets, configuración y código
comprobados mantienen sus hashes; no hubo operaciones de escritura de Git ni
acceso a producción. Las exigencias curriculares y académicas del plan siguen
vigentes.

**Aplicación confirmada; resultado registrado a continuación:** aplicar únicamente
las reparaciones 9 → 7 en una copia experimental nueva, archivando contexto y
conservando evaluación, etiquetas y orden de las filas restantes. Mantener
Francisca como alta separada. Antes de entrenar hay que fijar la evaluación por
obras/documentos y elegir una sola hipótesis de comparación; todavía no se
autoriza un entrenamiento con esta propuesta.

## Bloque actual cerrado: copia experimental del corpus v2

Se aplicó únicamente la operación 9 → 7 aprobada en el bloque anterior. El nuevo
export está en `outputs/corpus-snapshot-v2/reviewed-export.json`; su
[registro verificable](../artifacts/reviews/corpus-snapshot-v2.json) identifica
entradas, script, salida, archivo de contexto y comprobaciones mediante hashes.
La referencia académica y el export padre de Villanueva permanecen intactos.

Resultado local: **596 train, 81 validación y 137 test, con las mismas nueve
fuentes de entrenamiento**. Se reemplazó solo el texto de siete filas y se
retiraron las dos filas cuyo contenido quedó repartido: índices parentales
25/149. Las otras 807 filas conservan contenido y orden relativo; también se
conservan etiquetas, tipos y fuentes de las filas reemplazadas. Los índices de
salida se guardan en el mapa de correspondencias, porque los retiros desplazan
las posiciones posteriores. Francisca y los candidatos condicionados no se
incorporaron. Coincidir con los 596 ejemplos del conjunto académico no hace
idénticos ambos datasets: sus textos y hashes son distintos.

`replacement-archive.json` conserva los nueve originales, sus 75 particiones
(9312 caracteres), siete unidades, los contextos actuales y los dos archivos
ancestrales de Fonseca/Villanueva. Las páginas textuales de O'Phelan están
incorporadas para evitar enlaces relativos ambiguos. Las páginas de Fonseca,
vacías en el resumen consolidado, se recuperaron de su propuesta verificada y
quedaron registradas por unidad. El historial previo permanece completo.
Las 144 palabras brutas retiradas de estas filas siguen como contexto, con el
coste de cobertura declarado en el bloque anterior.

**Verificación local:** once comprobaciones del constructor, incluidas rechazo
de cambios en evaluación, etiquetas, texto, excepción de longitud, archivo
incompleto, inclusión de Francisca, hash incorrecto y destino existente o ajeno
a `outputs/`. Se verificaron los objetos resultantes fila por fila y la copia
guardada. Los controles de similitud no encontraron alertas en los candidatos;
el duplicado previo 709/737 se conserva en los nuevos índices 707/735. No se
declara eliminado todo duplicado del corpus.

El constructor reproducible es `scripts/build_corpus_snapshot_v2.py`. Exige
las entradas locales verificadas y una carpeta de salida nueva:

```powershell
python scripts/build_corpus_snapshot_v2.py --output outputs/corpus-snapshot-v2-reproduced
```

El script reutiliza herramientas existentes y no instala dependencias. No
sobrescribe datos, no invoca mantenimiento, entrenamiento ni servicios. Los
JSON con textos y contexto quedan en `outputs/`, fuera de Git; el script y el
registro ligero pueden versionarse. Los hashes de archivos y de JSON canónico
se identifican por separado. Otra máquina necesitará las entradas locales.

**Estado:** implementación y aplicación local verificadas; ninguna nueva
comprobación en producción, inferencia o métrica del modelo. Cinco de las siete
unidades reparadas todavía superan 192 tokens y la validez temática sigue basada
en revisión asistida por IA. La limitación de validación de una sola fuente y su
reutilización permanece. Las obligaciones de ambas unidades académicas siguen
vigentes; esta copia no sustituye sus demostraciones pendientes.

El bloque de preparación de fuentes y reserva de evaluación fue confirmado por
la autora; su resultado se registra a continuación. No se autorizó aquí un
entrenamiento ni una incorporación automática al snapshot.

## Diversidad de fuentes y reserva de evaluación — preparación cerrada

El [registro del lote](../artifacts/reviews/source-diversity-v1.json) conserva
textos, atribuciones, licencias, localizadores, hashes y decisiones. Se examinaron
nueve candidatos y se preparó una variante de uno de ellos: son **diez versiones,
no diez ejemplos independientes**. Se proponen seis para una futura copia local.
Los PDF, imágenes, extracciones originales, contextos completos y auxiliares
quedan en `outputs/source-diversity-v1/`, excluido de Git. El registro permite
leer la propuesta en otro equipo; repetir todo el cotejo requiere esos materiales.

### Unidades propuestas y fronteras

| Unidad | Fuente y páginas impresas | Palabras / tokens BETO | Categoría propuesta y aporte |
|---|---|---:|---|
| CON2011-P103-104 | Contreras, 103–104 | 198 / 270 | Republicana: consecuencias de la guerra sobre comercio, capital y producción; no relato de operaciones militares |
| CON2011-P111 | Contreras, 111 | 212 / 272 | Colonial: instituciones y crédito minero; 1786 fecha las ordenanzas, no el inicio demostrado del declive |
| CON2011-P125 | Contreras, 125 | 167 / 223 | Republicana: cambios tributarios 1821–1826; distinguir medidas y aplicación efectiva |
| CON2011-P127 | Contreras, 127 | 203 / 262 | Republicana: propuestas fiscales 1827/1836; alternativa proyectos políticos conservada, sin afirmar que se aprobaron |
| HUN-02 | Hünefeldt, 87–88 | 229 / 282 | Social/regional: demandas propias de cimarrones; interpretación referida a grupos concretos, no a toda población afrodescendiente |
| HUN-03B | Hünefeldt, 87 | 157 / 194 | Republicana: retorno a haciendas y restricciones de 1825; no presentar la Junta de Hacendados como ley nacional comprobada |

Las denominaciones abreviadas remiten a las categorías existentes de la guía.
HUN-03B contiene tres oraciones consecutivas del párrafo original: se conservan
las primeras 53 palabras como contexto. Evita la apertura con «estos grupos»
sin inventar ni identificar su referente. No incorporar simultáneamente HUN-03 y su variante.
Las preguntas educativas del registro son propuestas propias vinculadas al mapa
curricular anterior; tercero de secundaria sigue pendiente de confirmación.

**Exclusiones conservadas:** HUN-01 tiene un desacuerdo entre reclutamiento
militar y participación social; queda ambiguo, sin nueva etiqueta de dataset.
MAJ01/02 tienen temas reconocibles de crisis y liderazgo, pero la obra de Majluf
queda en cuarentena para entrenamiento: el control documental encontró su título
citado en la fuente de Sánchez reservada a test y una referencia compartida a
«Generosidad cívica», 25 de agosto de 1821. Es una decisión conservadora por relación
entre obras; no se demostró copia literal de los dos extractos seleccionados.
Este lote propone aportes a tres ejes. Los otros tres quedan con candidatos
ambiguos o retenidos, no declarados ausentes del entrenamiento.

### Fuentes y grupos documentales

[Contreras 2011, *Histórica* 35(2), 101–132](https://revistas.pucp.edu.pe/index.php/historica/article/view/3849)
y [Hünefeldt 1979, *Histórica* 3(2), 71–88](https://revistas.pucp.edu.pe/index.php/historica/article/view/7858)
tienen autoría y CC BY 4.0 comprobadas en sus fichas individuales. Se conserva la
atribución y el aviso de cambios de extracción. No se reutilizan balances de
Contreras que llegan a 1870/1876 como si describieran únicamente 1780–1842.

Son dos **obras** adicionales, no dos fuentes históricas independientes
certificadas. Fonseca cita Hünefeldt y ambos remiten a Miller en ediciones
distintas. Contreras modera el video ya usado en train, según la
[convocatoria oficial PUCP](https://facultad-ciencias-sociales.pucp.edu.pe/eventos/comision-bicentenario-y-mas-historiografia-y-politica-en-la-independencia-del-peru/).
No se comprobó qué filas pertenecen a cada voz. También se descartó como autora
nueva para evaluación a Elizabeth Hernández, ponente de esa mesa. La posible
versión Contreras 2010 se agrupa con 2011; su licencia no se intercambia entre ediciones.

Se reservan para **evaluación externa**, excluidas del próximo entrenamiento:

- [Natalia Sobrevilla Perea 2021, campañas a los puertos intermedios](https://kar.kent.ac.uk/101763/), *Revista de Indias* 81(281), 115–141, CC BY 4.0. PDF accesible. Registrar discrepancias del título/idioma de Kent y DOI `.04`/`.004`; no normalizarlas silenciosamente.
- [Núria Sala i Vila 2011, ayuntamientos del Trienio Liberal](https://revistadeindias.revistas.csic.es/index.php/revistadeindias/article/view/877/0), *Revista de Indias* 71(253), 693–728, CC BY 4.0. Ficha y bibliografía consultadas; PDF completo pendiente de acceso.

Sobrevilla cita Sala y documentos presentes en la bibliografía de train. Antes
de separar conjuntos se cotejarán los documentos concretos; una cita común es
una señal de revisión, no prueba automática de filtración. Ambas obras tienen
la misma revista y se concentran en 1820–1824: no aseguran cobertura completa
de 1780–1842, de las siete clases ni de varios contextos por categoría.

### Diseño propuesto y comprobaciones

La reserva de obras está documentada; **no existe todavía una evaluación nueva
congelada**. El siguiente paso es delimitar y revisar sus unidades sin ver
predicciones, excluir documentos repetidos y contar los soportes reales. Su
tamaño será el saldo de unidades admisibles, sin fabricar cuotas. Antes de
experimentar se guardarán textos, etiquetas, exclusiones, grupos y SHA-256.
No repartir al azar párrafos de una misma obra entre desarrollo y prueba final.

Con estas dos obras solo se plantea un desarrollo externo exploratorio. Se
compararán referencia y candidato sobre exactamente las mismas filas: F1 macro,
resultados/soportes por categoría, confusiones y por obra. Si faltan clases, se
declarará la lista utilizada y no se comparará ese macro parcial directamente
con 0.43766. Una prueba final nueva y separada continúa pendiente; un resultado
exploratorio no autoriza sustituir producción. La validación original de 81 filas
sigue siendo de una fuente y ya reutilizada.

Los diez textos/variantes pasan hashes, recuentos, offsets y reproducción de la
normalización. Hubo 8140 comparaciones con el corpus y 45 entre versiones: ninguna
alerta salvo el solapamiento deliberado padre/variante. La ausencia de alertas
léxicas no garantiza independencia documental. Hubo cotejo visual de páginas y
segunda revisión IA sin primeras etiquetas, aunque con contexto del recolector;
no se presenta como validación humana ni se calcula una métrica de acuerdo.

**Los seis propuestos superan 192 tokens, cuatro superan 256 y ninguno 384**, con
tokens especiales incluidos. No se midió cuánto afecta cada recorte al F1.
Se mantiene separada una futura comparación de longitud 192/384, otra de alta
de datos y otra sobre normalización del error ponderado. No se cambiaron esos
parámetros ni se cargaron pesos para esta comprobación.

Una incorporación posterior llevaría train 596→602 y fuentes 9→11; es una
proyección. Basadre pasaría de 244/596 (40.94%) a 244/602 (40.53%): este lote pequeño
no resuelve la concentración ni justifica prometer mejora. El dataset conserva
596/81/137, las etiquetas y sus hashes. Se conservaron los cambios previos del
README, del comparador y del control BETO.

Incidencia registrada: una inspección inicial de estructura mostró por error una
fila de validación al incluir la clave `items`. No se usó para elegir temas o
etiquetas; las inspecciones posteriores separaron train y los controles de
evaluación solo emitieron integridad/coincidencias. No se afirma ceguera completa
del agente principal respecto de esa validación ya reutilizada.

**Estado:** propuesta y comprobaciones locales; cero filas incorporadas, cero
entrenamientos, predicciones o métricas nuevas y ninguna acción en producción.
Se mantienen los entregables académicos de ambas unidades. **Siguiente bloque
propuesto en ese momento:** preparar el desarrollo externo con las dos obras
reservadas y congelar su alcance real antes de comparar modelos. La autora lo
confirmó; el resultado de ese bloque se registra a continuación.

## Desarrollo externo parcial congelado — 7 de septiembre de 2026, Lima

El [dataset separado](../artifacts/datasets/external-development-v1.json) contiene
**31 párrafos**, con sus textos, etiquetas, fuentes y páginas. El
[registro de revisión](../artifacts/reviews/external-development-v1.json) conserva
el inventario, ambas lecturas IA, adjudicaciones y exclusiones. No reemplaza los
81 ejemplos originales de validación ni constituye un test final nuevo.
La referencia y la copia reparada conservan **596 train / 81 val / 137 test**;
las seis adiciones de Contreras/Hünefeldt siguen siendo propuestas.

Se censaron 100 unidades de cuerpo: 98 párrafos narrativos y dos citas en bloque.
La regla previa exigía párrafos completos de 120–250 palabras, dentro de
1780–1842 y con argumento autónomo, sin unirlos o cortarlos para completar cuotas.
De las 43 unidades de longitud admisible, 39 pasaron a segunda lectura sin la
primera etiqueta; las cuatro retenidas recibieron una auditoría adicional,
conociendo sus motivos de retención. Las 100 unidades tienen estado final:
31 incluidas y 69 fuera del conjunto, con motivo registrado.

| Categoría evaluable | Sala 2011 | Sobrevilla 2021 | Total |
|---|---:|---:|---:|
| Crisis e ideas emancipadoras | 17 | 0 | 17 |
| Participación social y regional | 6 | 0 | 6 |
| Campañas y conflictos militares | 2 | 2 | 4 |
| Liderazgos, diplomacia y proyectos | 0 | 2 | 2 |
| Organización y consecuencias republicanas | 1 | 1 | 2 |
| **Total** | **26** | **5** | **31** |

**Antecedentes coloniales y `no_relevante` no quedan evaluados por este conjunto.**
Esto describe su soporte, no demuestra ausencia de esos temas en los artículos.
La métrica principal futura será F1 macro sobre las cinco clases presentes,
fijadas en `metric_labels`; se acompañará de soportes y resultados por clase/obra,
matriz de confusión con las siete etiquetas y predicciones hacia clases sin
soporte. Ese macro parcial no se comparará directamente con el antiguo 0.43766.

Las fuentes son [Sala i Vila (2011), pp.693–728](https://revistadeindias.revistas.csic.es/index.php/revistadeindias/article/view/877)
y [Sobrevilla Perea (2021), pp.115–141](https://kar.kent.ac.uk/101763/), ambas con
CC BY 4.0 y atribución en el dataset. Se preservan las discrepancias editoriales
de Sobrevilla y las dudas puntuales de Sala. La descarga pública de Sala requirió
desactivar la verificación TLS tras fallos de certificado; se registraron el
incidente, metadatos y hash, sin afirmar que el hash autentique al servidor.

El cotejo mecánico de los 39 candidatos realizó 63 726 comparaciones contra la
referencia, la copia reparada y las seis adiciones propuestas; no hubo alertas
de duplicación según los umbrales declarados ni entre candidatos. Once citas
marcadas de ocho o más palabras tampoco coincidieron exactamente con el corpus.
La evaluación antigua solo se usó para estos controles mecánicos, sin leer sus
etiquetas o contenidos para decidir la selección. La ausencia de alertas no
demuestra independencia documental: Sobrevilla cita Sala y ambas comparten
referencias con train. Se agrupa el documento concreto y sus ediciones; la
colección CDIP por sí sola no identifica un documento único.

Tres unidades quedan ambiguas; otras conservan dudas históricas, falta de
autonomía o longitud incompatible. `SOB-P024` queda en cuarentena provisional:
cita la ley de Riva Agüero del 1 de marzo de 1823 y Basadre train menciona el
adiestramiento de milicias, pero no permite identificar esa misma ley. No se
afirma filtración demostrada. Las decisiones IA no son validación humana
independiente ni garantía de exactitud de todas las afirmaciones de los autores.

El [verificador](../scripts/verify_external_development.py) comprueba el hash
del conjunto, adjudicación, etiquetas, recuentos y procedencia. El modo local
también coteja 26 archivos de entrada, los PDF y cada texto con su extracción.
Pasaron ambos modos y 13 controles de alteraciones en memoria; los archivos
congelados permanecieron intactos. No se ejecutaron entrenamientos ni inferencia.

```powershell
outputs/venv-ml/Scripts/python.exe scripts/verify_external_development.py
outputs/venv-ml/Scripts/python.exe scripts/verify_external_development.py --check-local-inputs
```

El primer comando usa los dos JSON versionados. El segundo requiere los archivos
locales ignorados, identificados por ruta/hash; PDF completos y salidas auxiliares
permanecen en `outputs/external-development-v1/`, fuera del commit. Huella canónica
del dataset: `0a12b4d4ac4b8ef58e561ed7c8632c73558454ec37edd8d269b9184fe49b6c82`.

Después de congelar se midió longitud con el tokenizador BETO local, sin pesos:
**28/31 superan 192 tokens, 16/31 superan 256 y ninguno supera 384**; rango 158–319,
incluidos tokens especiales. Estos recuentos no decidieron la selección ni
demuestran que ampliar la entrada mejore el F1.

**Estado:** preparado y comprobado localmente; modelo, corpus y producción sin
cambios. Es desarrollo exploratorio pequeño, concentrado en una obra y en
1820–1824, con dependencia entre fuentes. No autoriza una sustitución en producción.
Se mantienen los entregables de ambas unidades y el público escolar aún por confirmar.
**Bloque confirmado y completado:** comparación local de longitud 192 frente
a 384 con el entrenamiento original congelado y la evaluación separada.
El protocolo y los resultados se registran a continuación; no se incorporaron
simultáneamente reparaciones, textos nuevos ni cambios en la ponderación.
Una evaluación final independiente continúa pendiente.

## Comparación BETO 192 frente a 384 — 7 de septiembre de 2026, Lima

**Resultado: mejora numérica mínima, insuficiente para considerar resuelto el
problema del modelo.** El [informe](../artifacts/experiments/beto-length-v1/report.json)
conserva métricas, confusiones, 31 resultados pareados y comprobaciones. El
[protocolo](../artifacts/experiments/beto-length-v1/protocol.json) se congeló antes
de obtener predicciones; sus criterios no se cambiaron después del resultado.

| Medida sobre el mismo desarrollo externo | Referencia 192 | Candidato 384 |
|---|---:|---:|
| F1 macro, cinco categorías presentes | 0.10000 | 0.13333 |
| Aciertos totales | 3/31 | 4/31 |
| Aciertos en Sala | 1/26 | 2/26 |
| Aciertos en Sobrevilla | 2/5 | 2/5 |
| F1 de campañas y conflictos militares | 0.50000 | 0.66667 |
| F1 de crisis e ideas, participación social, liderazgos y organización republicana | 0 en las cuatro | 0 en las cuatro |

Cambian cinco predicciones: `SAL-P052` pasa de error a acierto y otras cuatro
siguen equivocadas; ningún acierto previo se pierde. Los 17 ejemplos de crisis
e ideas continúan sin aciertos. El candidato predice siete de ellos como contexto
colonial y diez como organización republicana. Esta confusión observada no
identifica una causa única ni demuestra que las etiquetas históricas sean falsas.

El resultado cumple **la señal exploratoria mínima** predeclarada: aumenta el
macro y no disminuyen aciertos totales ni por obra. No se confunde ese criterio
con calidad suficiente: 27 de 31 respuestas siguen erradas. Tampoco se compara
0.13333 con el antiguo 0.43766, calculado sobre otra evaluación y siete clases.
No se predijeron ni puntuaron nuevamente validación antigua o test.

Se conservó el entrenamiento original de 596 filas, incluidos textos, etiquetas
y orden. No entraron las reparaciones ni los seis textos nuevos propuestos.
Solo cambió `max_len`, de 192 a 384, tanto al entrenar como al inferir; este
experimento no separa esos dos efectos.

| Parámetro | Valor conservado |
|---|---|
| BETO base y revisión | `dccuchile/bert-base-spanish-wwm-cased`, `c4d86612f51b4f46759c8390d1798c2febe71b93` |
| Semilla y tasa de aprendizaje | 42; `2e-5` |
| Microbatch y acumulación | 2; 8 microbatches, tamaño nominal 16 |
| Optimizador, decay y clipping | AdamW; 0.01; norma máxima 1.0 |
| Pérdida | Frecuencia inversa por clase; media ponderada dentro de cada microbatch, normalización original conservada |
| Memoria y precisión | Gradient checkpointing y precisión mixta CUDA |
| Checkpoint comparado | Época 2 fija, heredada de la referencia existente |
| Calendario de aprendizaje | Horizonte de 3 épocas: 114 pasos nominales y 11 de calentamiento |

No se puso simplemente `epochs=2`: eso habría cambiado también el calendario.
El nuevo [entrenador](../scripts/beto_fixed_epoch.py) se detiene y guarda una vez
tras la época 2, manteniendo el horizonte original de tres. Recibe únicamente
train y no selecciona por validación. El [comparador](../scripts/compare_beto_length.py)
reutiliza el checkpoint de 192 y evalúa ambos sobre exactamente las 31 filas
congeladas, verificando 23 entradas y los archivos de la revisión base en caché.

El entrenamiento registró 70.16 s; el tramo de comparación medido, 79.62 s.
PyTorch registró máximos de 2.22 GB asignados y 2.42 GB reservados en la RTX 3050
local. Hubo 76 intentos de actualización: 75 aplicados y uno omitido por la
protección numérica de AMP, conforme a la política original. El informe de 192
no registraba esas omisiones; no se afirma igualdad de actualizaciones efectivas.
No hubo falta de memoria, reintentos de entrenamiento, descargas ni uso de Modal.

Comprobaciones: equivalencia bit a bit de pesos y tasas de aprendizaje hasta la
época 2 en un modelo sintético CPU; 11 controles del comparador, con 126 casos
de métricas contrastados con scikit-learn; 22 comprobaciones del recálculo
independiente de los resultados reales a partir de las predicciones archivadas; evaluación externa
y sus 26 archivos locales íntegros después de ejecutar. La prueba sintética no
certifica igualdad numérica en CUDA. Se conservan las limitaciones de una sola
semilla, dos obras relacionadas y etiquetas revisadas por IA.

Reproducción local, en una carpeta de salida nueva y con los archivos requeridos:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/compare_beto_length.py --protocol artifacts/experiments/beto-length-v1/protocol.json --output outputs/beto-length-v1-reproduction
```

Ese comando **sí entrena**; queda documentado, no se ejecutó una repetición.
Pesos, fixtures y salidas auxiliares permanecen en `outputs/beto-length-v1/`,
excluidos de Git. El candidato se conserva localmente y **no se seleccionó para
producción**. Implementación y ejecución local comprobadas; ninguna acción ni
verificación remota de producción en este bloque. Los cambios previos del
comparador de validación y del informe del control se conservaron.

**Siguiente bloque propuesto:** preparar un lote diverso a partir de la auditoría
del entrenamiento y del mapa de los seis ejes. Priorizar ejemplos con fronteras
claras entre instituciones virreinales, ideas políticas y organización republicana,
sin abandonar participación, economía y guerra; reutilizar las propuestas de
fuentes ya verificadas. Conservar las ambigüedades y no cambiar etiquetas del
desarrollo para mejorar la métrica. Esta evaluación ya fue utilizada: evitar
encadenar ajustes sobre ella y mantener pendiente una prueba final independiente.
Esperar confirmación de la autora antes de iniciar ese bloque. Se mantienen los
entregables académicos de las dos unidades.

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
