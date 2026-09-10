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
| Preparación del lote diverso v3 | Preparar aportes trazables y revisar fronteras del entrenamiento | 231 textos leídos; 31 altas propuestas de cinco obras para cinco ejes; 12 fronteras pendientes de resolver. Corpus intacto, sin entrenamiento ni mejora nueva demostrada |
| Resolución de fronteras v3 | Cotejar las 12 filas y definir cambios exactos | Contexto recuperado y cuatro dependencias identificadas. Propuesta: nueve unidades y siete cuarentenas; 30 altas previas conservadas, HUN-03B retenido. Simulación 596→589→619 train, sin aplicar ni entrenar |
| Aplicación y comparación BETO v3 | Medir el paquete de datos con receta fija | Copia local de 619 train y 14 fuentes. Una ejecución: F1 externo parcial 0.13333→0.13333, mismos 4/31 aciertos; tres predicciones cambiaron y siguieron incorrectas. Candidato no seleccionado; producción intacta |
| Diagnóstico de ajuste BETO en train | Comprobar si las categorías se reconocen en datos conocidos | Dos inferencias locales, sin reentrenar. Candidato: ideas 47/75, participación 68/89 y liderazgos 53/101; externamente siguen en cero. En 560 filas comunes: 426→431 aciertos, pero ideas 36→30. Ajuste parcial y diferencia entre train y desarrollo, sin causa única demostrada |
| Contraste BETO por obras y épocas | Retener obras completas y contrastar épocas 2 y 3 | Dos trayectorias locales: ideas retenidas O'Phelan 0/28→0/28 y Morán 0/14→0/14. Ideas en fit 34/44→32/44 y 26/61→41/61. La tercera época no resuelve la transferencia; resultado dependiente de la obra, sin selección de modelo |
| Revisión contrastiva de ideas | Comparar cuatro errores y ocho controles de TRAIN | 12 pasajes completos a 384 tokens. Cortes heredados en O'Phelan; dos controles de ideas y un control social requieren una regla historiográfica uniforme. Morán mantiene etiquetas temáticamente defendibles. Sin cambios de datos, entrenamiento o causa única demostrada |
| Cierre de frontera historiográfica | Decidir los tres casos señalados con una regla uniforme | Propuesta cerrada: cuarentena de 697/577 y reclasificación de 49 a no_relevante. Simulación 619→617 train, 14 fuentes y evaluación intacta. No aplicada; no demuestra mejora de BETO |
| Control comparable TF-IDF/BETO | Ejecutar dos ajustes sobre las mismas particiones v3 | Ideas: TF-IDF 1/28 y 5/14 frente a BETO 0/28 y 0/14. Diferencia útil en Morán, mínima en O'Phelan; sin ganador general, causa única ni modelo promovido. Dos ajustes y 21 resúmenes verificados |
| Ensayo de tasa BETO | Cambiar solo lr2e-5→4e-5 en época 2 | Ideas retenidas: O'Phelan 0/28→0/28, Morán 0/14→3/14. Mejora de ajuste en ambas particiones; criterio conjunto incumplido. Dos trayectorias, 14 resúmenes verificados, sin promoción |
| Revisión ciega y piloto de siete clases | Revisar unidades con un agente sin etiquetas previas y preparar fuentes reservadas | 12 pasajes de train revisados; 26 candidatos nuevos →22 aceptados y4 apartados. Siete clases,125–229 palabras,166–331 tokens. Revisión IA, sin gold humano ni independencia documental plena; no se ejecutaron modelos |
| Normalización de pérdida BETO | Corregir el objetivo ponderado sobre el grupo acumulado | Pruebas de gradientes aprobadas y dos entrenamientos completados. Ideas retenidas: O'Phelan 0/28→0/28; Morán 0/14→1/14. Sin mejora suficiente; 14 resúmenes verificados. Variante experimental conservada, sin promoción |
| Limpieza adjudicada de TRAIN v4 | Aplicar decisiones históricas y medir su efecto con receta fija | 619→613 TRAIN, seis cuarentenas y una reclasificación; 22 controles del agente aprobados. Dos entrenamientos: ideas O'Phelan 0/28→0/28, Morán 1/14→2/14. Criterio incumplido; 18 resúmenes verificados, sin promoción |
| Capacidad básica y cobertura | Separar memorización, calidad de unidades y variedad de subtemas | BETO aprende 28/28 ejemplos repetidos, con 100 actualizaciones. Revisión de 70 ideas: 30 unidades para revisar; fuentes y subtemas están asociados. Ninguna idea se recorta a 384 tokens. Prioridad: unidades y fronteras coherentes, luego cobertura comparable entre obras; sin mejora de generalización demostrada |
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

La autora confirmó la preparación del lote diverso. Su resultado se registra
a continuación. El desarrollo externo ya fue utilizado: evitar encadenar ajustes
sobre él y mantener pendiente una prueba final independiente.

## Preparación del lote diverso v3 — bloque cerrado

Registro: [training-batch-v3.json](../artifacts/reviews/training-batch-v3.json).
Se prepararon **31 altas de cinco obras, sin incorporarlas al corpus**. Se leyeron
los textos completos de 231 filas de entrenamiento de la copia reparada v2:
71 de antecedentes coloniales, 60 de crisis e ideas y 100 de organización
republicana. Esto cubre esas tres categorías, no los 596 textos ni el contexto
original completo de cada obra. Las observaciones se vinculan a índices y hashes;
los recuentos de rasgos de extracción proceden de lectura asistida por IA y no
equivalen a tasas de etiquetas incorrectas.

La concentración comprobada es alta: Basadre aporta 52/71 textos coloniales;
O'Phelan y una mesa de historiografía, 47/60 de ideas; Basadre y Orrego, 85/100
republicanos. Sí hay soberanía, juntas, ciudadanía, fiscalidad y relaciones
laborales en los textos leídos. Las carencias propuestas distinguen calidad y
contexto de ausencia: no se declara ausente un tema por una búsqueda de palabras.

La revisión señala **12 filas actualmente coloniales cuya frontera necesita
contexto y adjudicación**, sin declararlas todas incorrectas ni republicanas.
El contraste más concreto es HUN-03B, propuesto como organización republicana,
frente a las filas 559 y 564 de la copia reparada, etiquetadas como antecedentes
coloniales: los pasajes describen restricciones a personas esclavizadas y normas
de los primeros años republicanos, incluido el reglamento de octubre de 1825.
No se ha certificado que reproduzcan el mismo documento primario. Es una tensión
observable entre etiquetas; no demuestra una causa única del bajo F1.

Las fuentes y unidades propuestas son:

| Obra verificada | Altas | Páginas impresas seleccionadas | Aporte principal | Licencia editorial |
|---|---:|---|---|---|
| [Carlos Contreras, 2011](https://revistas.pucp.edu.pe/index.php/historica/article/view/3849) | 4 | 103–104, 111, 125, 127 | Minería colonial, consecuencias económicas y fiscalidad republicana | CC BY 4.0 |
| [Christine Hünefeldt, 1979](https://revistas.pucp.edu.pe/index.php/historica/article/view/7858) | 2 | 87–88 | Agencia afrodescendiente y regulación de la esclavitud | CC BY 4.0 |
| [María José Arguedas Pinasco, 2022](https://revistas.pucp.edu.pe/index.php/conexion/article/view/26124) | 1 | 97 | Actuación política de Francisca Zubiaga, con atribuciones conservadas | CC BY 4.0 |
| [Teodoro Hampe Martínez, 2010](https://bdigital.uncu.edu.ar/8023) | 6 | 82–83, 85–88 | Proyecto monárquico y misiones diplomáticas | CC BY-NC-SA 3.0 |
| [Luis Daniel Morán, 2019](https://revistas.ucm.es/index.php/HICS/en/article/view/64491) | 18 | 202, 204–208, 210–215 | Prensa, legitimidad política, gobierno provisional y discursos de participación | CC BY 4.0 |

Autoría, publicación, enlaces, páginas, condiciones de reutilización y cambios
de extracción están registrados por obra y fragmento. Hampe conserva atribución,
uso no comercial y compartir igual; no se declara una licencia uniforme para el
corpus. Las citas de terceros conservan su procedencia y sus límites de cotejo.
Las cartas transmitidas por Burzio y la traducción moderna de Tristán permanecen
retenidas donde sus condiciones no se resolvieron. Tampoco se incorporan las tres
cartas diplomáticas previas con licencia pendiente; acceso gratuito no la resuelve.

Se reutilizan siete propuestas anteriores. Para las dos obras nuevas se
inventariaron 85 unidades: 33 de las secciones 4–6 de Hampe y 52 del cuerpo del
artículo de Morán. De las 40 unidades de 120–250 palabras, se proponen 24, se
excluyen ocho por contenido metodológico o argumento incompleto y se retienen
ocho por ambigüedad, autonomía insuficiente o condiciones de reutilización.
Las otras 45 no cumplen ese intervalo y no se recortaron para completar una cuota.
Francisca conserva la excepción nominal previa de 114 palabras de la guía.
Las lecturas separadas de los candidatos nuevos ocultaron la primera etiqueta;
los desacuerdos y la adjudicación posterior se conservan. Son revisiones de IA,
no validación humana independiente.

Distribución propuesta: **1 colonial, 14 ideas, 5 participación social, 0 militares,
7 liderazgos/proyectos, 4 republicanos y 0 no relevantes**. Se amplían cinco ejes.
Guerra sigue pendiente de otra obra utilizable: mencionar Suipacha o Guaqui en un
argumento sobre propaganda no convierte ese párrafo en operaciones militares.
Las 14 altas de ideas proceden de Morán; no son 14 fuentes independientes.
Se mantienen juntas las versiones y los documentos citados relacionados al
diseñar futuras separaciones de datos. Una coincidencia temática no prueba fuga.

Como interpretación pedagógica propia del mapa curricular ya documentado, los
pasajes permiten comparar exhortación y participación efectiva, proyecto y
aplicación, y cambios y permanencias después de 1821. Por ejemplo, las propuestas
fiscales de CON2011-P127 no se presentan como medidas efectivamente ejecutadas.
Estas preguntas se relacionan con interpretar fuentes, comprender el tiempo
histórico y elaborar explicaciones en el [programa del MINEDU, pp. 45 y 48](https://www.minedu.gob.pe/curriculo/pdf/programa-curricular-educacion-secundaria.pdf).
Tercero de secundaria sigue siendo una hipótesis pendiente de confirmación;
no se adaptó el producto ni se añadieron etiquetas.

Si posteriormente se añadieran las 31 propuestas sin otros cambios, la copia
reparada pasaría de **596 a 627 filas de train y de 9 a 14 obras/recursos**.
Basadre conservaría sus 244 filas: su peso bajaría del 40,94 % al 38,92 %.
La diversificación es limitada y no resuelve por sí sola la concentración ni
la cobertura regional. Esta es una proyección, no un dataset creado; las futuras
reparaciones podrían modificarla. Las 31 altas son distintas de las 31 filas del
desarrollo externo.

Comprobaciones locales: 31 textos y hashes contrastados con sus registros de
origen; 231 observaciones enlazadas al entrenamiento; extracción de las dos obras
nuevas reproducida y páginas seleccionadas cotejadas visualmente. El examen de
los 47 candidatos elegibles y reutilizados realizó 77 973 comparaciones mecánicas
contra referencia, copia reparada y desarrollo externo, más 1 081 pares internos:
sin alertas por igualdad, inclusión textual o los umbrales de similitud registrados.
Eso no certifica independencia documental. Los 31 seleccionados caben en 384
tokens; 23 superan 192, medidos con el tokenizador local sin inferencia.
El control separado del consolidado aprobó 29 comprobaciones y verificó los 12
archivos protegidos antes de editar este plan; después, los otros 11 permanecen
intactos. Validación, test y desarrollo externo no cambiaron. No se utilizaron
textos o predicciones de evaluación para adjudicar las altas. Se conserva la
incidencia de exposición accidental de líneas de revisión del desarrollo durante
una búsqueda demasiado amplia; no se presenta el proceso como completamente ciego.

**Implementado:** propuesta y registro de revisión. **Probado localmente:**
integridad, procedencia y comprobaciones anteriores. Sin entrenamiento, nuevas
predicciones, métricas ni mejora nueva demostrada; ninguna acción o verificación
en producción. El último contraste de longitud continúa mostrando solo un acierto
adicional en una evaluación pequeña ya utilizada. No se concluye que los
hiperparámetros sean la causa del problema. La validación original sigue limitada
a una fuente y reutilizada; el desarrollo externo tampoco es una prueba final.

Los textos propuestos, decisiones y trazabilidad quedan en el JSON versionable.
PDF completos, páginas, imágenes, auxiliares y el control de cierre permanecen
locales en `outputs/training-batch-v3/`, excluidos de Git; repetir todo el cotejo en
otro equipo requiere recuperarlos. Los cambios previos del comparador y del
control de reproducción no forman parte de este bloque.

La autora confirmó la resolución de las fronteras. La propuesta de cambios y sus
consecuencias se registran a continuación; no se han aplicado al entrenamiento.

## Resolución de fronteras v3 — propuesta cerrada, sin aplicar

Registro: [boundary-resolution-v3.json](../artifacts/reviews/boundary-resolution-v3.json).
Se cotejaron las 12 filas con sus páginas originales. Cuatro filas adicionales
contienen partes de los mismos argumentos: **298, 560, 561 y 763**. El mapa
abarca, por tanto, 16 originales; no equivale a 16 etiquetas demostradas incorrectas.
Los índices corresponden a `outputs/corpus-snapshot-v2/reviewed-export.json`.
Los hashes permiten identificarlos también en el entrenamiento de la referencia
congelada, donde están los 16 textos originales.

El tema queda adjudicado para la propuesta en nueve de las 12 filas: siete
republicanas, una social/regional y una de ideas. Las otras tres —548, 556 y 558—
requieren conservar la incertidumbre o separar unidades de distinto foco. La
adjudicación temática no significa que el texto actual sea apto sin reparación.
Una segunda lectura ocultó etiquetas anteriores y primera propuesta; se conservan
sus desacuerdos. Dos límites finales se comprobaron después con la propuesta
visible. Todas son revisiones asistidas por IA, no validación humana experta.

La propuesta concreta es sustituir ocho textos y reclasificar nueve filas, dejando
otras siete temporalmente fuera de **una futura copia local**. Ninguna se convierte
en `no_relevante`; los originales, restos y alternativas permanecen archivados.

| Posición futura | Unidad propuesta | Palabras | Etiqueta propuesta y motivo |
|---:|---|---:|---|
| 68 | PER-R68-RURAL | 225 | Social/regional: propiedad y actividades rurales; el padrón de 1826 es evidencia, no una regla automática para etiquetar |
| 69 | PER-R69-DEC | 159 | Republicana: consecuencias agrarias desiguales de guerra y rebelión, con la reserva de Huertas conservada |
| 552 | BAS-552 | 134 | Republicana: ministerios y representación exterior como estructura administrativa de 1828 |
| 556 | BAS-556 | 138 | Republicana: estimaciones demográficas y crítica explícita al uso de cifras de 1795; conserva la tabla necesaria |
| 558 | BAS-558-social | 208 | Social/regional: reclutamiento y posición ocupacional de grupos; recupera también material de 763 |
| 560 | BAS-558-norma | 126 | Republicana: servicios personales, ciudadanía y tutela indígena; reúne la norma de 558 con su continuación en 560 |
| 562 | BAS-562 | 181 | Republicana: integración de extranjeros y comercio; texto exactamente idéntico, solo cambia la etiqueta propuesta |
| 564 | BAS-564 | 185 | Republicana: disposiciones favorables a hacendados y su justificación económica atribuida, sin presentar esta como opinión del revisor |
| 565 | BAS-565 | 133 | Ideas: regalismo, jansenismo y circulación de impresos en 1825/1833; separa la cita inicial cortada |

Las posiciones **298, 532, 548, 559, 561, 763 y 765** se proponen para cuarentena
en esa copia. Algunos contenidos se recuperan en la tabla; otros quedan retenidos.
El mapa conserva el coste de cobertura: enumeración territorial, inventario naval,
partes sobre situación indígena, alimentación/vestido de personas esclavizadas y
otros contextos no se trasladan íntegramente a las nueve unidades. Los 16 originales
suman 3 231 palabras; las nueve unidades, 1 489. Esa diferencia no mide hechos
históricos perdidos y no autoriza a declarar ausentes sus temas en todo el corpus.

El cotejo de esclavitud resolvió la frontera temática y detectó reservas concretas:

- 559 comienza con el final de una memoria de **1846** cuya atribución y fecha
  quedaron fuera del fragmento. Además, el reglamento continúa en 561 antes de
  llegar a 564; unir únicamente los dos extremos perdería contenido.
- La [transcripción de Núria Sales, 1970, pp. 328–331](https://bibliotecadigital.inah.gob.mx/janium/Documentos/IPGH/REHIAM_00_0070_1970_P279.pdf)
  identifica una disposición del Consejo de Gobierno fechada el **14/10/1825**;
  su nota 72 cita la *Gaceta* del **16/10**. Basadre dice «publicado» el 14.
  No se corrige silenciosamente la diferencia ni se afirma haber cotejado la Gaceta original.
- HUN-03B queda **retenido**, aunque su tema republicano esté confirmado: no se
  demostró una ratificación de la Junta el día 14 ni que su resumen sobre
  manumisión corresponda a una cláusula del reglamento. El registro anterior de
  31 propuestas se conserva intacto; ahora se proponen **30 altas**, sin ese texto.

Otras reservas quedan delimitadas: el párrafo de 298 mezcla una referencia a los
primeros diez años del XIX con bienios posteriores; el recorte limpio de 548 tiene
119 palabras y no recibe una excepción. Los pasajes de 532 y 765 contienen la
denominación «Constitución de 1827», mientras que el [texto oficial del Congreso](https://www3.congreso.gob.pe/Docs/sites/webs/constitucion/constituciones/Constitucion1828.pdf)
con ese preámbulo corresponde a 1828. Se retienen las versiones completas hasta
documentar cómo presentar esa diferencia. El cierre de 765 sí está en el impreso:
no se inventa continuación. Su autora citada es **Pilar García Jordán**, 1993,
pp. 53–54, reproducida en la página 234 del libro; no atribuir automáticamente
todo el PDF a Basadre.

Se identificó la edición local de Basadre: e-book de noviembre de 2014, Cantabria,
ISBN 978-612-306-354-2, con derechos reservados en PDF 28. El [capítulo oficial de
Pereyra, 2016](https://repositorio.pucp.edu.pe/items/f2c23330-ffb6-453e-94d4-295186c63316/full)
coincide con el PDF local y declara **CC BY-NC-ND 2.5 PE**. El registro versionable
conserva decisiones, límites y huellas; los pasajes reconstruidos completos siguen
en `outputs/boundary-resolution-v3/`. No se declara autorizada la redistribución
del corpus adaptado ni se emite una conclusión jurídica sobre pesos futuros.

| Escenario simulado; ninguno aplicado | Train | Colonial | Ideas | Social | Militar | Proyectos | Republicana | No relevante |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Copia reparada v2 actual | 596 | 71 | 60 | 83 | 87 | 94 | 100 | 101 |
| Nueve unidades y siete cuarentenas | 589 | 56 | 61 | 84 | 87 | 94 | 106 | 101 |
| Lo anterior más las 30 altas propuestas | 619 | 57 | 75 | 89 | 87 | 101 | 109 | 101 |

Comprobado localmente: originales y ubicaciones, reconstrucción mediante offsets
y cambios de formato explícitos, particiones de Pereyra y ocho páginas de Basadre
cotejadas visualmente. Las nueve unidades cumplen 120–250 palabras. El control
mecánico realizó 7 731 comparaciones contra las filas que se conservarían, el
desarrollo externo y las 30 altas, más 36 pares entre unidades: sin alertas con
los umbrales registrados. Las coincidencias con los originales retirados están
documentadas como dependencias, no ocultadas como ausencia de duplicados.
La simulación conserva exactamente las otras 798 filas y su orden relativo,
incluidas las 81 de validación y las 137 de test. El desarrollo externo de 31
filas permanece intacto; sus textos y etiquetas no se interpretaron para decidir.
El control separado del consolidado aprobó 40 comprobaciones, con cero fallos.
Verificó los 13 archivos protegidos antes de actualizar este plan y los otros 12
intactos después; `git diff --check` pasó. Su informe queda localmente en
`outputs/boundary-resolution-v3/closing-check.json`.

**Implementado:** adjudicación y mapa exacto de cambios. **Probado localmente:**
extracción, integridad y simulación. No se creó un dataset nuevo, no se aplicaron
etiquetas ni se entrenó; no hay métricas nuevas ni mejora de BETO demostrada.
Ninguna acción o verificación en producción. Este paquete cambia conjuntamente
textos, etiquetas y cantidad: su comparación futura no aislará automáticamente
la contribución de cada componente ni demostrará una causa única del bajo F1.

**Propuesta aprobada y ejecutada en el bloque siguiente:** aplicar este mapa a
una copia local, incorporar separadamente las 30 altas y fijar el protocolo antes
de una sola comparación local de BETO con referencia y receta constantes. La
pregunta será si el paquete de datos mejora el resultado; no añadir búsquedas de
semilla, longitud o función de pérdida. El desarrollo ya utilizado dará evidencia
exploratoria; test no elegirá el candidato y sigue pendiente una prueba final
independiente. Se mantienen el periodo, las siete etiquetas, tercero de secundaria
como hipótesis y los entregables académicos de ambas unidades.

## Aplicación y comparación BETO v3 — bloque cerrado

**No hubo mejora en el desarrollo externo:** F1 macro de cinco clases
**0.13333→0.13333**, con los mismos **4/31 aciertos**. Se conserva la referencia;
el candidato queda local y no se selecciona para producción.
[Protocolo previo](../artifacts/experiments/beto-data-v3/protocol.json),
[aplicación](../artifacts/experiments/beto-data-v3/application.json) y
[resultados y comprobaciones](../artifacts/experiments/beto-data-v3/report.json).

La copia `outputs/corpus-snapshot-v3/reviewed-export.json` contiene 619 train,
81 validación y 137 test. Sobre v2 se aplicaron nueve sustituciones/reclasificaciones,
siete cuarentenas y 30 altas de cinco obras; HUN-03B continúa retenido. Las 798
filas ajenas al mapa conservaron contenido y orden relativo; las 218 de evaluación
son idénticas también a la referencia original. Hay 14 fuentes en train, frente
a nueve. Se conservaron originales, procedencia y un duplicado heredado; no se
introdujeron duplicados exactos normalizados en las unidades cambiadas.

La comparación incluye **todo el paquete**, también las reparaciones v2:
560 filas coinciden exactamente en fuente/texto/etiqueta con el train original;
36 originales ya no coinciden y 59 filas del candidato son nuevas o cambiadas.
No permite atribuir el resultado a una corrección, fuente o hiperparámetro.

Se reutilizaron pesos y predicciones de BETO de 384 tokens sobre train de 596 filas. El candidato
partió de BETO base con revisión fijada, semilla 42, AdamW, tasa `2e-5`, longitud 384,
microbatch 2 y acumulación 8; checkpoint de época 2 con horizonte de tres épocas.
La fórmula de pesos inversos por clase y la normalización por microbatch se
conservaron. Por aumentar las filas, el horizonte pasó de 114 a 117 pasos y los
intentos de 76 a 78: hubo 77 actualizaciones y un salto AMP. Entrenamiento local
offline de 69.39 s, sin reentrenar la referencia ni seleccionar épocas nuevas.

| Categoría evaluada | Soporte | F1 antes | F1 después |
|---|---:|---:|---:|
| Campañas y conflictos militares | 4 | 0.66667 | 0.66667 |
| Crisis e ideas emancipadoras | 17 | 0 | 0 |
| Liderazgos, diplomacia y proyectos | 2 | 0 | 0 |
| Organización y consecuencias republicanas | 2 | 0 | 0 |
| Participación social y regional | 6 | 0 | 0 |

Sala mantuvo 2/26 aciertos y Sobrevilla 2/5. Solo cambiaron SAL-P001/P022/P041,
de antecedentes coloniales a organización republicana; los tres eran de ideas
y continuaron incorrectos. Las predicciones fueron militares 8→8, coloniales 11→8
y republicanas 12→15; las otras categorías no se predijeron en estos 31 ejemplos.
Eso es un patrón comprobado, **no una explicación causal**. La pérdida de train
bajó de 1.78024 a 1.18979; esa reducción no demuestra generalización.

**Verificación local:** seis pruebas del constructor, seis del aislamiento del
runner y doce controles independientes del resultado con scikit-learn aprobados;
26 entradas congeladas intactas. No se hicieron nuevas predicciones de validación
original ni test, ni acciones o verificaciones en producción. Los 31 externos ya
se reutilizaron, proceden de dos obras relacionadas, solo cubren cinco clases y
su revisión asistida por IA no es validación humana independiente. Estos resultados
no son comparables directamente con el F1 original 0.43766 de otra validación.
Corpus completo, originales, contextos y pesos permanecen en `outputs/`, fuera de
Git; reproducir el bloque requiere esas entradas locales y sus permisos específicos.

**Propuesta aprobada y ejecutada en el bloque siguiente:** usar los checkpoints
existentes para comprobar si ideas, participación y liderazgos también fallan en
train. Ese diagnóstico medirá ajuste al entrenamiento, no calidad final; ayudará
a distinguir un problema de aprendizaje de uno de transferencia entre fuentes.
Sin nuevos entrenamientos ni ajuste de etiquetas por predicción. La evaluación
final independiente de siete clases sigue pendiente.

Comandos para registrar este bloque y las dos revisiones previas aún pendientes
(no incluyen el comparador modificado previamente por la autora, PDFs ni pesos):

```powershell
git add -- coursework/README.md scripts/build_training_batch_v3.py scripts/compare_beto_data_v3.py artifacts/reviews/training-batch-v3.json artifacts/reviews/boundary-resolution-v3.json artifacts/experiments/beto-data-v3/protocol.json artifacts/experiments/beto-data-v3/application.json artifacts/experiments/beto-data-v3/report.json
git commit -m "Evalua lote historico v3 de BETO con protocolo fijo"
```

## Diagnóstico de ajuste BETO en train — bloque cerrado

**BETO reconoce parcialmente las siete categorías en entrenamiento**, incluidas
las tres sin aciertos externos. Se usaron los dos checkpoints guardados de época 2
y longitud 384; no se entrenó ni cambió ningún modelo.
[Script](../scripts/diagnose_beto_training_fit.py),
[protocolo previo](../artifacts/experiments/beto-training-fit-v1/protocol.json) y
[resultado auditado](../artifacts/experiments/beto-training-fit-v1/report.json).

| Categoría | Referencia: aciertos en su train | Candidato: aciertos en su train | Externo, ambos modelos |
|---|---:|---:|---:|
| Crisis e ideas | 37/59 | 47/75 | 0/17 |
| Participación social y regional | 67/83 | 68/89 | 0/6 |
| Liderazgos, diplomacia y proyectos | 49/93 | 53/101 | 0/2 |

En sus respectivos entrenamientos, la referencia obtuvo 450/596 aciertos y F1
macro de siete clases 0.74478; el candidato, 475/619 y 0.76029. **Son poblaciones
distintas:** esa diferencia no demuestra mejora. El candidato aún falla en 28
de las 75 ideas y 48 de los 101 liderazgos de su propio entrenamiento.

El contraste sobre **las mismas 560 filas** (559 identidades distintas y un
duplicado heredado) pasó de 426 a 431 aciertos y F1 macro de 0.74967 a 0.75415.
Corrigió 28 errores e introdujo 23. Ideas bajó de 36/56 a 30/56 aciertos;
participación, de 65/79 a 62/79; liderazgos subió de 48/92 a 49/92.
El informe conserva también precisión, recall, F1, confusiones y resultados por obra.

Las 30 incorporaciones obtuvieron 21 aciertos; entre ellas, las ideas de Morán
obtuvieron 13/14. Las otras 29 filas exclusivas del candidato, procedentes de
reparaciones o reclasificaciones en fuentes anteriores, obtuvieron 23 aciertos.
Son ejemplos que el candidato ya vio al entrenar: **no miden generalización**.

El hallazgo es ajuste incompleto a train y una diferencia marcada con las dos
obras externas evaluadas. No prueba por sí solo memorización, sobreajuste, un
problema de extracción, etiquetas equivocadas o hiperparámetros incorrectos.
No corresponde cambiar etiquetas por predicción ni elegir más épocas con esta
evidencia. El F1 externo de cinco clases permanece en 0.13333 y no se compara
directamente con los macros de siete clases de train.

**Implementado y probado localmente:** 1 215 predicciones en dos cargas de modelo,
23.17 s de ejecución; siete controles previos y doce comprobaciones independientes
con scikit-learn aprobadas, 26 entradas congeladas intactas. Se reutilizaron las
métricas externas guardadas; no hubo inferencia nueva externa, de validación
original o test, ni acciones o verificaciones en producción. Las predicciones
por fila y la auditoría completa están en `outputs/beto-training-fit-v1/`;
el informe versionable referencia sus hashes y evita copiar textos del corpus.

**Propuesta confirmada y ejecutada en el bloque siguiente:** evaluar generalización
por obras completas dentro de TRAIN, declarando grupos, comparación y coste local
antes de ejecutar. Se reutiliza el diagnóstico previo entre fuentes, sin barrido
de hiperparámetros ni más ajustes sobre los 31 externos. La evaluación final
independiente de siete clases sigue pendiente; se mantienen el periodo,
la taxonomía y los entregables académicos.

Comandos adicionales para este diagnóstico. Si el bloque anterior sigue sin
registrar, ejecutar también su comando `git add` antes del commit:

```powershell
git add -- coursework/README.md scripts/diagnose_beto_training_fit.py artifacts/experiments/beto-training-fit-v1/protocol.json artifacts/experiments/beto-training-fit-v1/report.json
git commit -m "Diagnostica ajuste de BETO en train sin reentrenar"
```

## Contraste BETO por obras y épocas — bloque cerrado

La autora confirmó ejecutar el contraste propuesto tras la auditoría independiente
del diagnóstico de ajuste. Pregunta: **¿las ideas se reconocen al excluir una obra
completa y mejora ese reconocimiento al completar la tercera época?** No se
busca un modelo ganador ni se vuelve a ajustar sobre los 31 externos.

La revisión documental de TRAIN cambió la primera partición antes de entrenar:
Huamanga/Pereyra cita y utiliza O'Phelan (1985) en pp. 173, 188 y 189 (filas
74, 78 y 276 del snapshot v3, índices base cero); la bibliografía en fila 352
identifica el artículo exacto.
Se retienen las dos obras juntas, conservando O'Phelan como resultado primario.
Morán conserva todas sus unidades y documentos primarios reproducidos juntos.
El rastreo de coincidencias no certifica independencia documental exhaustiva;
la revisión es asistida por IA, no adjudicación humana independiente.

| Ronda | Filas para aprender | Obras retenidas | Resultado primario |
|---|---:|---|---|
| O'Phelan + Huamanga | 459 | O'Phelan: 103 y Huamanga: 57 | Ideas de O'Phelan: 28; Huamanga se informa aparte |
| Morán | 601 | Morán: 18 | Ideas de Morán: 14 |

Se conserva TRAIN v3 de 619 filas, textos, etiquetas, orden relativo y las siete
clases. Dos inicializaciones desde BETO base fijado, semilla 42, AdamW lr 2e-5,
decay 0.01, max_len 384, microbatch 2, acumulación 8, clipping 1, checkpointing y
AMP float16. La CE ponderada conserva la media por microbatch y normalización
por grupo real. Pesos inversos calculados exclusivamente con las filas para
aprender de cada ronda. Horizontes de tres épocas: 87/114 pasos nominales y
calentamiento 8/11; se registran actualizaciones efectivas y saltos AMP.

Cada trayectoria guarda **épocas 2 y 3**, sin reiniciar optimizador, scheduler o
escalador y sin inferencia entre épocas. El entrenador histórico queda intacto;
una variante se comprueba contra él mediante módulos sintéticos en CPU. Esa
comprobación no certifica igualdad numérica CUDA. Tras entrenar se evalúan ambos
guardados sobre exactamente las mismas filas de fit y las obras retenidas.

Decisión previa: aumentos estrictos de aciertos de ideas en fit y en la obra
primaria, en ambas rondas, serían señal exploratoria de aprendizaje adicional
con transferencia. Si ambas mejoran fit sin aumentar aciertos primarios,
persiste la dificultad de transferencia. Otros patrones son inconclusos o
dependientes de la obra. Se acompañan aciertos/recall de precisión, F1 y
confusiones por clase y obra; macro solo sobre etiquetas con soporte declarado.
No se mezclan macros con diferentes soportes ni se elige época por resultados.

Coste previsto: 3–6 minutos de ejecución local y aproximadamente 1.8 GB para cuatro
checkpoints, aparte de preparación y verificaciones. Un fallo se registra y
detiene la ejecución, sin reintentar entrenamientos automáticamente. Protocolo,
hashes, particiones y dependencias se congelan antes del primer entrenamiento
en `artifacts/experiments/beto-source-epochs-v1/protocol.json`; pesos y
predicciones quedan locales en `outputs/beto-source-epochs-v1/`.

Los dos grupos son un diagnóstico de TRAIN elegido con evidencia previa,
no evaluación final independiente. Excluir obras cambia cantidad, composición,
pesos y calendario: no aísla estilo, calidad de etiquetas ni memorización.
Completar una época solo contrasta ese intervalo de aprendizaje. Validación
original, test y externos no reciben inferencia; no se cambian datos o etiquetas,
producción, servicios de pago ni Git.

**Resultado verificado:** completar la tercera época no produjo ningún acierto
nuevo de ideas en las dos obras primarias retenidas. La dificultad observada no
queda limitada a Sala/Sobrevilla: también aparece en estos grupos de TRAIN.
No se ha demostrado una causa única ni que todas las recetas o duraciones
posibles fallen. El estado predeclarado es `inconclusive_or_work_dependent`,
porque ideas en fit mejora en una ronda y baja en la otra.

| Medida pareada | Época 2 | Época 3 |
|---|---:|---:|
| Ideas en fit, ronda O'Phelan–Huamanga | 34/44 | 32/44 |
| Ideas retenidas, O'Phelan | 0/28 | 0/28 |
| Ideas retenidas, Huamanga (secundario) | 0/3 | 0/3 |
| Ideas en fit, ronda Morán | 26/61 | 41/61 |
| Ideas retenidas, Morán | 0/14 | 0/14 |
| Todos los aciertos retenidos, O'Phelan | 34/103 | 37/103 |
| Todos los aciertos retenidos, Huamanga | 27/57 | 27/57 |
| Todos los aciertos retenidos, Morán | 2/18 | 2/18 |

El macro de O'Phelan, con siete clases presentes, pasó de 0.21880 a 0.24036.
El de Morán, con tres clases presentes, pasó de 0.18095 a 0.18462, aunque
conservó los mismos dos aciertos. No se comparan esos macros entre obras.
En fit, el macro de siete clases subió en ambas rondas (0.75094→0.77364 y
0.72718→0.79509); eso no demuestra transferencia de ideas. En época 3, las
ideas de O'Phelan se confundieron sobre todo con participación y organización
republicana (11 casos cada una); las de Morán, con liderazgos (9 de 14).
Estas confusiones describen predicciones, no adjudican etiquetas.

Se ejecutaron exactamente dos trayectorias desde la base, cuatro guardados y
2 476 predicciones exclusivamente de TRAIN, en 223.51 s de ejecución medidos.
O'Phelan–Huamanga: 79.33 s de entrenamiento, 86 actualizaciones y un salto AMP;
Morán: 100.91 s, 114 actualizaciones y cero saltos. Máximo CUDA: 2.22 GB
asignados y 2.42 GB reservados; cuatro checkpoints y tokenizadores: 1.76 GB.
Las cifras usan GB decimales. No hubo reintentos de entrenamiento.

Pasaron 12 controles sintéticos sobre el código final, incluida equivalencia
bit a bit con el entrenador histórico en épocas 2 y 3, y el recálculo separado
con scikit-learn de 68 resúmenes de métricas. Se comprobaron 114 archivos por
hash, las 2 476 identidades de predicción, los contadores y tasas del scheduler,
los pesos de clase y las 218 filas originales de evaluación intactas.

Evidencias: [protocolo previo](../artifacts/experiments/beto-source-epochs-v1/protocol.json),
[resultados](../artifacts/experiments/beto-source-epochs-v1/report.json) y
[recálculo verificable](../artifacts/experiments/beto-source-epochs-v1/verification.json).
Implementación: `scripts/beto_epoch_trajectory.py`,
`scripts/compare_beto_source_epochs.py`, `scripts/check_beto_source_epochs.py`
y `scripts/verify_beto_source_epochs.py`. Los corpus, pesos y predicciones
siguen locales; reproducir requiere las entradas protegidas disponibles.
Los runners rechazan sobrescrituras o repetir este experimento ya existente.

No se seleccionó época ni modelo; no se cambiaron datos, etiquetas, checkpoints
anteriores o producción. Validación original, test y los 31 externos no
recibieron nuevas predicciones. Se conservan los cambios previos de la autora
en `scripts/compare_beto_validation.py`. Bloque terminado; se espera
confirmación antes de iniciar otro contraste.

## Revisión contrastiva de ideas — bloque cerrado

La autora confirmó revisar 12 pasajes sin reentrenar ni cambiar etiquetas:
cuatro errores retenidos (dos por obra), cuatro ideas acertadas en fit y cuatro
ejemplos acertados de las clases confundidas. «Acertado» significa coincidencia
con la etiqueta guardada, no certificación histórica.

Selección congelada antes de leer los pasajes: en época 2, las dos confusiones
más frecuentes por obra; un error de cada grupo por hash con semilla 42. Para
cada error, el control léxico más próximo de ideas y el de la clase confundida,
ambos acertados en fit de la misma ronda, sin repetir ninguna de las 12 filas.
La similitud de conjuntos de palabras solo sirve para seleccionar controles.

Pregunta limitada: coherencia de tema dominante entre obras, presencia del
argumento en la entrada real de 384 tokens y ejemplos comparables encontrados
en entrenamiento. Se reutilizan revisiones existentes vinculadas por hash.
El contenido completo, recorte exacto y contexto quedan locales. Se comprobó
que los IDs y máscaras coinciden con `_loader`, además de pertenencia y hashes.

No es una muestra ciega ni representativa, no estima una tasa de errores y no
demuestra ausencia temática en todo TRAIN. Es revisión asistida por IA, no
validación histórica humana independiente. La conclusión distinguirá problemas
concretos de anotación, recorte o cobertura pendiente; si no discrimina causas,
lo declarará. Test, validación original y externos quedan fuera del análisis.

**Resultado:** los 12 segmentos tienen entre 167 y 286 tokens, incluidos los
especiales, y entran completos en 384. Aumentar la ventana no mostraría texto
adicional en estos casos; no se extrapola esta conclusión a todo el corpus.

| Error retenido, índice de snapshot v3 | Lectura contrastiva |
|---|---|
| O'Phelan 127 → participación | Facciones radical/moderada y regionalismo: ideas es compatible, con frontera social. La unidad comienza y termina cortada y mezcla notas; el PDF permite recuperar contexto |
| O'Phelan 194 → organización republicana | Programa fiscal de La Paz en 1809, con efectos sociales; el parecido fiscal con Contreras 1821–1826 no basta para cambiar la etiqueta. Inicio amputado y antecedente ausente |
| Morán 826 → liderazgos | Plan explícito de circulación clandestina del Diario Secreto de 1811. La revisión previa respalda ideas y conserva las elipsis y la lectura impresa «va que» |
| Morán 820 → organización republicana | Crisis de 1808, juntas y propaganda Buenos Aires–Lima: argumento autónomo y etiqueta ideas respaldada por revisiones previas |

Los índices son base cero. Los cortes observados en O'Phelan ya pertenecen al
segmento del corpus: **no los causa el tokenizador**. Se consultó la capa textual
de las páginas PDF 10–12 y 33–34, sin incorporar texto ni certificar visualmente
anomalías del impreso. Esos cortes no explican por sí solos los dos errores de
Morán, cuyos argumentos pertinentes están visibles.

Los controles de ideas 697 y 577 son discusión/preguntas historiográficas y ya
habían sido señalados en el diagnóstico F03. BETO coincide con sus etiquetas,
pero eso no certifica su adecuación. El control social 49 también discute método
historiográfico: necesita la misma regla de pertinencia. No se propone convertir
automáticamente esos tres casos en `no_relevante`, excluir toda historiografía
moderna o descartar textos por proceder de video.

La cobertura temática general existe: el control 242 contiene juntas y autonomía
en fit de la ronda Morán. Además, HUE02/03/04, previamente revisados por propaganda,
lecturas políticas y prensa, conservan sus hashes y pertenecen a fit en ambas
rondas. Se reutilizaron sus dictámenes sin ampliar la lectura de la muestra.
Los vecinos léxicos seleccionados son débiles contrastes semánticos; no demuestran
ausencia de subtemas en todo TRAIN. Cobertura fina y representación aprendida
siguen sin aislarse causalmente.

**Verificación:** nueve controles finales aprobados, 127 archivos únicos
comprobados por hash, 12 identidades y roles confirmados, y coincidencia exacta
de entradas mediante `_loader` y una comprobación separada con `tokenizers`.
Se vinculó revisión previa por hash exacto para 10 de los 12 textos. Las 218
filas originales de evaluación permanecen idénticas. La exportación inicial
falló por serializar `BatchEncoding`; se convirtió a diccionario y se verificó
que las 12 selecciones y roles no cambiaron. El cotejo usa el ID real de `[PAD]`
del vocabulario BETO, 1, sin asumir el valor 0.

Evidencia: [selección congelada](../artifacts/reviews/beto-ideas-contrast-v1-selection.json),
[revisión de los 12 pasajes](../artifacts/reviews/beto-ideas-contrast-v1.json) y
[comprobaciones locales](../outputs/beto-ideas-contrast-v1/verification.json).
Preparador: `scripts/prepare_beto_ideas_contrast.py`; textos, contexto y auxiliares
permanecen en `outputs/beto-ideas-contrast-v1/`, excluidos de Git. No se entrenó,
no se cargó un clasificador ni se generaron predicciones nuevas. Datos, etiquetas,
modelos anteriores y cambios previos de la autora quedaron intactos.

**Decisión confirmada y preparada en el bloque siguiente:** formular una regla
uniforme y cerrar los casos 697/577/49, sin ampliar taxonomía ni aplicar cambios.
Los casos 127/194 quedan separados como reparaciones de unidades: no combinar
ambas intervenciones en otro paquete sin un contraste definido.

## Control comparable TF-IDF frente a BETO por obras

La autora autorizó dos ajustes locales de TF-IDF con el corpus v3 intacto de
619 filas de train. Se reutilizan exactamente las particiones congeladas del
contraste BETO: O'Phelan y Huamanga retenidos juntos (459 fit, 160 retenidos,
103 de O'Phelan como resultado principal), y Morán (601 fit, 18 retenidos).
Se conserva TF-IDF de palabras y bigramas, C=4, semilla 42, una CPU y la función
existente `fit_tfidf`. Vocabulario y clasificador se ajustan solo con cada fit.

Antes de ejecutar: época 2 de BETO como referencia; época 3 secundaria, sin
seleccionar época. Se medirán aciertos, F1 macro sobre clases presentes y sobre
las siete clases, confusiones por categoría y errores corregidos/nuevos sobre
las mismas filas. Los resultados de fit serán únicamente descriptivos.
Si TF-IDF aumenta aciertos de ideas y F1 macro de clases presentes en ambas
obras principales, se investigará la receta/representación de BETO. Si ambos
métodos siguen sin acertar ideas en ambas obras, se priorizarán datos entre
obras y evaluación revisada independientemente antes de ajustar hiperparámetros.
Los demás resultados se considerarán mixtos, sin ganador. Son señales
exploratorias, no pruebas causales ni evaluación independiente final.

Las tres correcciones historiográficas permanecen como propuesta. No se
reentrena BETO ni se predice sobre validación, test o los 31 ejemplos externos.
El bloque termina después de dos ajustes y la verificación, sin nuevas variantes.
Protocolo y resultados: `artifacts/experiments/tfidf-beto-work-control-v1/`;
modelos y predicciones locales: `outputs/tfidf-beto-work-control-v1/`.

**Resultado ejecutado y verificado:** exactamente dos ajustes, convergencia
sin advertencias (25 y 35 iteraciones). El tiempo de ajuste y predicción registrado
fue 0.80 y 1.06 segundos, sin incluir importaciones y verificaciones de archivos.

| Obra principal retenida | Modelo | Aciertos totales | Aciertos de ideas | F1 macro de clases presentes |
|---|---|---|---|---|
| O'Phelan | BETO época 2 | 34/103 | 0/28 | 0.218804 |
| O'Phelan | BETO época 3, secundaria | 37/103 | 0/28 | 0.240361 |
| O'Phelan | TF-IDF C=4 | 34/103 | 1/28 | 0.220198 |
| Morán | BETO época 2 | 2/18 | 0/14 | 0.180952 |
| Morán | BETO época 3, secundaria | 2/18 | 0/14 | 0.184615 |
| Morán | TF-IDF C=4 | 7/18 | 5/14 | 0.425439 |

O'Phelan tiene soporte en siete clases; Morán solo en tres. Los F1 macro de
siete clases para Morán son 0.077551, 0.079121 y 0.182331, respectivamente.
No comparar el F1 entre obras como si tuvieran la misma distribución.
TF-IDF corrige cinco errores de BETO en Morán sin introducir otros; en O'Phelan,
frente a época 2, corrige 15 e introduce 15. Participación en O'Phelan cae de
13/18 a 5/18 aciertos, mientras liderazgos permanece en 2/21. Por ello, recuperar
un caso de ideas no representa una mejora uniforme de categorías.
En Huamanga, resultado secundario, TF-IDF acierta 23/57 frente a 27/57 de BETO
en ambas épocas; ideas permanece en 0/3. El agregado retenido O'Phelan–Huamanga
es 57/160 para TF-IDF frente a 61/160 y 64/160 para BETO.

La regla congelada produce `signal_to_investigate_beto_recipe_or_representation`:
ideas y F1 aumentan frente a época 2 en ambas obras principales. **Su umbral
era cualquier incremento positivo, no una diferencia estadística ni útil por
definición.** En O'Phelan el F1 sube apenas 0.001394 y no supera época 3;
la señal relevante se concentra en Morán. No se declara superioridad general
de TF-IDF ni un defecto demostrado del entrenamiento BETO.

TF-IDF acierta todos sus ejemplos de fit (459/459 y 601/601), mientras BETO
mantiene ajuste parcial. Esto demuestra que esta representación puede separar
las etiquetas de entrenamiento; no demuestra que sean correctas ni que TF-IDF
generalice bien. Las diferencias incluyen representación, optimización y
longitud visible: TF-IDF usa el texto completo; BETO conserva máximo 384 tokens.
No se ha aislado cuál explica las diferencias observadas.

**Decisión de modelamiento:** cerrar este control sin otro entrenamiento ni
promoción. Hay señal aprendible en algunos casos que la receta actual de BETO
no recupera; tampoco basta cambiar a TF-IDF para resolver la transferencia.
El siguiente ensayo, si se autoriza, deberá aislar una sola intervención del
ajuste BETO con criterio fijado antes de ejecutarlo; estas obras reutilizadas
solo servirán como desarrollo. La selección final sigue necesitando evaluación
independiente y revisada, con las siete clases. No se justifica otro barrido
indefinido ni aplicar las tres correcciones como supuesta solución causal.

Verificación: 21 resúmenes recalculados con scikit-learn, 1 238 filas de
predicciones alineadas, 2 476 identidades BETO cotejadas, pares de errores
verificados y las 218 filas de validación/test idénticas. Protocolo, entradas
heredadas y cuatro archivos de salida protegidos por hash. El primer intento
de guardar el protocolo detectó que faltaba crear la carpeta; se corrigió antes
de congelarlo y antes de cualquier ajuste. No hubo entrenamiento repetido.
Evidencia: [protocolo](../artifacts/experiments/tfidf-beto-work-control-v1/protocol.json),
[resultados](../artifacts/experiments/tfidf-beto-work-control-v1/report.json) y
[verificación](../artifacts/experiments/tfidf-beto-work-control-v1/verification.json).

## Ensayo de una variable BETO: tasa de aprendizaje

La autora autorizó el contraste mínimo posterior. Pregunta: ¿duplicar la tasa
de aprendizaje mejora el ajuste y la transferencia de ideas en época 2?
Se cambia únicamente `lr=2e-5` a `4e-5`, una intervención predefinida, no una
tasa óptima conocida. La motivan el ajuste parcial BETO y los casos de Morán
recuperados por TF-IDF; esto no demuestra que la tasa anterior fuera incorrecta.

Se conservan las dos particiones del corpus v3, datos y orden, semilla 42,
base/revisión offline, 384 tokens, ponderación y normalización de pérdida,
AdamW, acumulación y horizonte de tres épocas del scheduler. Se usa el mismo
entrenador ya verificado, sin modificarlo; se detiene en época 2 y se compara
con las predicciones existentes de época 2. Se registran los saltos AMP y
actualizaciones efectivos, que pueden diferir por la trayectoria numérica.

Criterio congelado antes de entrenar: al menos dos aciertos adicionales de
ideas en **cada** obra principal retenida, sin descenso de F1 macro de siete
clases en ninguna de ellas y sin descenso de aciertos de ideas en ninguno de
los dos fit. Si solo mejora ideas en ambos fit pero no en las obras, se informa
mejor ajuste sin transferencia. Los demás casos no satisfacen el criterio o
dependen de la obra. El umbral es exploratorio, no significación estadística
ni calidad suficiente para uso automático.

Se ejecutarán exactamente dos trayectorias nuevas, una por partición, sin
repetir la referencia, sin tercera época ni otras tasas. No se aplican las
tres correcciones ni se infiere sobre validación/test/desarrollo externo.
El bloque termina con resultados, verificación y decisión, sin promover modelo.
Evidencia: `artifacts/experiments/beto-learning-rate-v1/`; pesos y predicciones
locales: `outputs/beto-learning-rate-v1/`.

**Ejecución completada:** dos trayectorias nuevas y dos checkpoints de época 2;
1 238 predicciones sobre filas del train original, con función fit/retenido
conservada por partición. Tiempo total registrado 167.85 segundos; entrenamiento
54.69 y 68.77 segundos. Pico CUDA: 2 219 309 568 bytes asignados y
2 422 210 560 reservados. Se usaron solo los pesos y dependencias locales.

| Partición y resultado | Referencia lr2e-5 | Intervención lr4e-5 |
|---|---|---|
| Fit sin O'Phelan–Huamanga: aciertos / ideas | 346/459; 34/44 | 373/459; 35/44 |
| Fit sin Morán: aciertos / ideas | 448/601; 26/61 | 509/601; 51/61 |
| O'Phelan retenido: aciertos / ideas | 34/103; 0/28 | 37/103; 0/28 |
| O'Phelan: F1 macro de siete clases | 0.218804 | 0.217740 |
| Morán retenido: aciertos / ideas | 2/18; 0/14 | 5/18; 3/14 |
| Morán: F1 macro de siete clases | 0.077551 | 0.124013 |
| Morán: F1 macro de sus tres clases presentes | 0.180952 | 0.289364 |

El F1 macro de fit sube 0.750937→0.811986 y 0.727182→0.839640.
La mayor tasa mejora el ajuste en ambas particiones y recupera tres ideas
retenidas de Morán; no resuelve ideas en O'Phelan. En esa obra, liderazgos
baja 2/21→0/21 y participación 13/18→11/18, por lo que más aciertos totales
no implica mejora uniforme. Huamanga, secundaria, sube 27/57→29/57 aciertos
y permanece en 0/3 ideas; el conjunto retenido O'Phelan–Huamanga pasa de
61/160 a 66/160 aciertos, con 0/31 ideas en ambos modelos.

**Decisión congelada: `criterion_not_met_or_work_dependent`.** Se incumplen
en O'Phelan tanto el incremento mínimo de ideas como la ausencia de caída
de F1. No se selecciona ni despliega el candidato. La respuesta al ajuste
sí aporta evidencia: algunos errores de Morán responden a esta intervención;
no se puede atribuir todo el fallo a textos imposibles de aprender. Tampoco
se demuestra que la tasa original explique todo el problema, que las etiquetas
sean correctas o que esta tasa sea óptima. Una sola semilla y obras reutilizadas
no permiten una conclusión general ni una afirmación de significación.

Contadores efectivos hasta época 2: O'Phelan–Huamanga 58 actualizaciones y
0 saltos en ambos modelos; Morán 76/0 en la referencia y 75/1 en el candidato.
El salto antiguo de O'Phelan mencionado durante el progreso pertenecía a la
tercera época, fuera de este contraste. En Morán hubo un salto en época 2
del candidato; no se afirma igualdad de pasos efectivos. Solo se cambió una
variable configurada, pero la trayectoria AMP y el scheduler por actualización
pueden responder a ese cambio. Se conservaron normalización de pérdida,
pesos por clase, semilla, tokenizadores y el resto de la receta.

Verificación final aprobada: cinco controles de la regla antes de entrenar,
14 resúmenes recalculados con scikit-learn, 1 238 identidades alineadas,
99 entradas protegidas y 18 archivos nuevos comprobados por hash. Se verificaron
mapeos de etiquetas, tokenizadores, pesos de clases, contadores y tasas del
scheduler. Las 218 filas de validación/test permanecen idénticas y no se
realizó inferencia sobre ellas ni sobre los 31 ejemplos externos. La guía,
el corpus real y las tres correcciones propuestas permanecen intactos.

**Siguiente decisión, sin ejecución adicional:** detener el barrido de
hiperparámetros. La evidencia identifica sensibilidad al ajuste y transferencia
dependiente de la obra; no exige descubrir una causa única para avanzar.
Priorizar ahora una revisión independiente de unidades completas y fronteras
entre ideas, participación y liderazgos en obras distintas, junto con una
evaluación nueva que cubra las siete categorías. Separar desde el inicio las
obras destinadas a enriquecer train de las destinadas a evaluación. Las
predicciones actuales sirven para señalar casos a revisar, nunca como gold
automático. BETO permanece como asistencia con revisión, sin calidad autónoma
demostrada. No se autorizó ni ejecutó en este bloque otra intervención de datos.

Evidencia: [protocolo](../artifacts/experiments/beto-learning-rate-v1/protocol.json),
[resultados](../artifacts/experiments/beto-learning-rate-v1/report.json) y
[verificación](../artifacts/experiments/beto-learning-rate-v1/verification.json).

## Contraste de capacidad básica y cobertura temática

Ante la pregunta de la autora sobre fuentes, entrenamiento o categorías,
se separan dos hipótesis: incapacidad básica para aprender las etiquetas y
cobertura insuficiente al cambiar de obra. El agente revisa los 70 TRAIN de
ideas por subtema y fuente, sin predicciones. Se auditan concentración por
fuente, longitud real del tokenizador e identidades de entrada a 384 tokens.
La asociación entre fuente y etiqueta es descriptiva; no prueba por sí sola
que BETO use atajos.

La prueba técnica usa una sola trayectoria del BETO fijado, con cuatro textos
PDF por clase (28), entradas distintas, 120–250 palabras y sin truncamiento.
La selección es determinista por hash, prioriza diversidad de fuentes y no
consulta predicciones. Repite el pequeño conjunto durante 50 épocas y un
máximo de 100 intentos de actualización, con lr 2e-5 y pérdida por grupo
acumulado. Se guarda únicamente la época 50 y se mide sobre esos mismos 28
textos. El criterio previo es 28/28; no hay prolongación adaptativa.

Esta prueba admite memorizar etiquetas equivocadas: no certifica calidad
histórica ni generalización. Tampoco recomienda 50 épocas para el corpus
completo. Pasarla limitaría la hipótesis de una incapacidad básica del modelo
y del entrenamiento bajo ese presupuesto; fallarla exigiría revisar la
optimización antes de añadir datos indiscriminadamente. La distinción entre
optimización y generalización también se estudia en
[Mosbach et al., ICLR 2021](https://arxiv.org/abs/2006.04884); sus resultados
en GLUE no demuestran la causa de este proyecto.

**Resultado: BETO aprendió los 28/28 textos repetidos**, cuatro por cada una
de las siete clases. Realizó 100 actualizaciones y cero omisiones AMP. La
[verificación](../artifacts/experiments/beto-learning-sanity-v1/verification.json)
recalculó matriz y F1 con scikit-learn, comprobó las 28 identidades, 185
entradas protegidas y nueve archivos generados. El presupuesto de repetición
es distinto del ensayo por obras: pasar este control no demuestra que dos
épocas del corpus completo basten ni descarta problemas más sutiles.

La auditoría del TRAIN v4 muestra lo siguiente:

| Evidencia | Resultado | Interpretación limitada |
|---|---|---|
| Longitud de ideas | 0/70 superan 384 tokens | Aumentar longitud no recuperaría texto truncado de esas unidades |
| Longitud total | 2/613 superan 384: índices v4 146 y 514 | Los recortes restantes no están en ideas |
| Entradas idénticas del tokenizador | Una pareja con la misma etiqueta militar; ninguna contradicción | No aparece un conflicto de etiquetas causado por entradas exactamente iguales |
| Concentración militar | 70/87 ejemplos de un único PDF | Cantidad de textos no equivale a diversidad de fuentes |
| Concentración colonial | 40/57 del mismo PDF | Cobertura desigual entre fuentes |
| Concentración republicana | 64/109 del mismo PDF | Concentración descriptiva, no prueba de un atajo usado por BETO |
| Ideas por fuentes | 70 textos de seis resourceId; 56 de tres de ellos | Algunos problemas históricos dependen de una sola obra |

Como control descriptivo, predecir la clase mayoritaria de la fuente usando
las etiquetas de sus otras filas alcanza 234/613, frente a 109/613 al usar
solo la mayoría global. Este cálculo usa información de la misma fuente;
no se presenta como rendimiento en fuentes nuevas ni como competidor de BETO.

El agente leyó las 70 unidades de ideas sin consultar predicciones. Su
[inventario](../artifacts/reviews/beto-root-cause-v1/ideas-coverage-review.json)
distingue 40 argumentos sustantivos, 15 fragmentarios, siete mixtos, siete
predominantemente metahistoriográficos y uno que requiere revisar alcance
temporal. Estas categorías descriptivas **no son nuevas etiquetas del modelo**.
Los [30 casos para revisión](../artifacts/reviews/beto-root-cause-v1/review-queue.json)
no son 30 errores de etiqueta demostrados. Tampoco los otros 40 constituyen
gold humano confirmado. Se verificaron hashes, extractos literales, las 70
identidades, seis resúmenes por fuente y siete tablas de cobertura por clase.

Dos vacíos concretos se observan entre esas 70 ideas: al retirar O'Phelan y
Huamanga faltan equivalentes desarrollados de legitimidad inca, programas
regionales de juntas y Cádiz en litigios indígenas. Al retirar Morán quedan
otros ejemplos de prensa, pero se pierde su circuito manuscrito clandestino
de 1811 y ciertas polémicas antijuntistas. Por tanto, los contrastes anteriores
cambian simultáneamente fuente y subtema; no aíslan exclusivamente estilo.
Ausencia aquí no significa ausencia en todas las otras clases del corpus.

El cotejo posterior con predicciones ya guardadas da 0/8 en los argumentos
O'Phelan inventariados como sustantivos y 2/14 en Morán. No hubo nueva
inferencia. Esta selección es exploratoria y no valida sus etiquetas; impide
dar por probado que todos los errores desaparezcan al retirar fragmentos.

**Prioridad técnica elegida:** estabilizar ejemplos y fronteras de ideas frente
a participación social y liderazgos, y luego cubrir los mismos subtemas con
obras distintas. La regla sigue siendo el argumento dominante: difusión y
legitimidad de ideas; agencia y coaliciones sociales; actuación y proyectos
de dirigentes. Mencionar un líder o una junta no decide automáticamente.
Los casos sin dominancia o unidad suficiente necesitan contexto o cuarentena,
sin inventar una octava clase.

El siguiente contraste mínimo se acota a la cola de 30 unidades: cotejar
originales, resolver dominancia y continuidad sin mirar predicciones y fijar
las sustituciones antes de entrenar. No aplicar exclusiones masivas basadas
solo en el inventario. Después se define un lote de cobertura con los mismos
problemas en otras obras y se controla dependencia documental. No hay una
cantidad mágica de textos ni evidencia suficiente para reemplazar BETO,
fusionar clases o recomendar más épocas indiscriminadamente. La estabilidad
entre semillas y el presupuesto del corpus completo siguen sin resolverse.

No se modificaron datos o etiquetas en este bloque ni se usó evaluación
original, externo 31, piloto 22 o producción. Evidencias:
[cobertura cuantitativa](../artifacts/reviews/beto-root-cause-v1/quantitative-coverage.json),
[protocolo de memorización](../artifacts/experiments/beto-learning-sanity-v1/protocol.json),
[resultado](../artifacts/experiments/beto-learning-sanity-v1/report.json) y
[runner](../scripts/diagnose_beto_learning_sanity.py).

## Limpieza adjudicada de TRAIN y comparación controlada v4

La autora solicitó continuar tras el ensayo de normalización. Se retomó la
revisión histórica pendiente y se aplicaron decisiones en una copia separada,
sin convertir predicciones del clasificador en etiquetas.

El agente cotejó cuatro unidades PDF con los originales locales de O'Phelan
y Orrego: siete páginas inspeccionadas visualmente y una adicional en texto.
La fila 643 se conserva porque contiene un argumento fiscal autónomo; sus
porcentajes OCR siguen sin corregirse y no deben citarse como datos fiables.
Las filas 127, 194 y 242 se apartan por cortes sustantivos de argumentos y
notas intrusivas. La anomalía verbal sobre papeles de deuda de 194 también
existe en el impreso; no se inventó un verbo para completarla.

También se apartan los videos 577, 675 y 697 por cortes y transcripción sin
audio/minutaje verificable. La fila 49 cambia de participación social a
`no_relevante` para esta tarea: desarrolla metodología historiográfica y no
un argumento histórico sustantivo del periodo, según las revisiones previas.
No se reclasifican como negativos los fragmentos inciertos.

La [copia v4](../outputs/corpus-snapshot-v4/reviewed-export.json) contiene
613 TRAIN, 81 validación y 137 test. Se conservan siete clases y 14 fuentes;
830 filas originales permanecen idénticas, una cambia solo de etiqueta y
seis se archivan en cuarentena. Ningún texto fue editado. El [informe de construcción](../artifacts/reviews/beto-training-cleanup-v1/build-report.json)
y la [verificación](../artifacts/reviews/beto-training-cleanup-v1/build-verification.json)
registran cada correspondencia. Es una limpieza de unidades seleccionadas,
asistida por IA, no una certificación humana del corpus completo.

Antes de entrenar se declara una sola comparación del paquete de datos contra
los checkpoints guardados de `beto-loss-normalization-v1`, manteniendo pérdida
por grupo acumulado, lr 2e-5, semilla 42, 384 tokens, época 2 y horizonte de
scheduler de 3. Las particiones tienen 456 y 595 ejemplos de ajuste. Pesos de
clase y orden aleatorio dependen de la nueva población: no se atribuirá el
resultado a una exclusión individual.

La comparación principal conserva las mismas obras completas y etiquetas:
103 textos de O'Phelan y 18 de Morán. La evaluación secundaria excluye las tres
unidades O'Phelan apartadas, de manera idéntica para ambos modelos; no decide
el ganador. Las métricas de ajuste usan los mismos supervivientes y la etiqueta
corregida de 49 para ambas predicciones. Se comprobó antes de entrenar que las
métricas principales guardadas se reproducen exactamente.

Criterio exploratorio: al menos dos aciertos adicionales de ideas en cada
obra principal, sin caída de F1 macro de siete clases ni de ideas en el ajuste
común. Máximo dos trayectorias y dos checkpoints; no se utilizan validación,
test, externo 31 ni piloto 22 para entrenar o evaluar. Las obras de TRAIN se
han reutilizado: sus resultados no son evaluación independiente.

**Resultado: copia y comparación completadas; criterio de mejora incumplido.**

| Obra principal | Ideas, referencia → v4 | Total correcto, referencia → v4 | F1 macro de siete clases, referencia → v4 |
|---|---|---|---|
| O'Phelan | 0/28 → 0/28 | 33/103 → 33/103 | 0.21397 → 0.20330 |
| Morán | 1/14 → 2/14 | 3/18 → 4/18 | 0.09048 → 0.10931 |

La referencia de esta tabla ya emplea la normalización corregida; no es el
modelo histórico anterior ni el ensayo de tasa. En los mismos supervivientes
de ajuste, O'Phelan/Huamanga pasa de 313/456 a 329/456 aciertos, pero ideas
baja de 34/42 a 33/42. En la ronda Morán, ideas mejora de 28/56 a 47/56,
mientras el total baja de 441/595 a 431/595. No se confunde este ajuste a
textos conocidos con capacidad para clasificar obras excluidas.

El subconjunto secundario de O'Phelan sin las tres unidades apartadas mantiene
0/25 ideas y 33/100 aciertos en ambos modelos; F1 macro 0.21522→0.20505.
Huamanga pasa de 31/57 a 30/57. Por tanto, ni filtrar las unidades problemáticas
de la evaluación secundaria elimina el problema observado.

Se ejecutaron dos trayectorias, dos checkpoints y 1 238 predicciones en
150.48 segundos. Pico CUDA: 2 219 310 592 bytes asignados. La ronda
O'Phelan/Huamanga realizó 58 actualizaciones, cero omisiones AMP, frente a
56 y dos de referencia. Morán mantiene 76 y cero en ambas. El paquete cambia
la composición, los pesos derivados y la trayectoria numérica; este ensayo
no separa sus efectos causales individuales.

La [verificación de métricas](../artifacts/experiments/beto-training-cleanup-v1/verification.json)
recalculó 18 resúmenes con scikit-learn y comprobó identidades, exclusión por
fuente, mapas de clases, tokenizadores, scheduler y decisión. El agente
recomputó [22 controles de aplicación del dataset](../artifacts/reviews/beto-training-cleanup-v1/dataset-peer-check.json),
todos aprobados, sin consultar predicciones. La copia y las decisiones quedan
conservadas; no se sustituye el modelo servido. El piloto 22 continúa sin
inferencias ni uso para ajustar modelos.

Conclusión limitada: estas seis exclusiones y una reclasificación no resuelven
el rendimiento entre obras. El resultado no invalida sus motivos históricos
ni demuestra que el resto del corpus esté bien segmentado o etiquetado.
Se cierra esta comparación; no se encadenan más hiperparámetros automáticamente.

[Protocolo previo](../artifacts/experiments/beto-training-cleanup-v1/protocol.json),
[informe](../artifacts/experiments/beto-training-cleanup-v1/report.json),
[Decisiones](../artifacts/reviews/beto-training-cleanup-v1/adjudication.json),
[cotejo del agente](../artifacts/reviews/beto-training-cleanup-v1/context-review.json),
[constructor](../scripts/build_beto_training_cleanup.py) y
[runner](../scripts/compare_beto_training_cleanup.py).

## Corrección experimental de la pérdida ponderada de BETO

La autora autorizó modificar el entrenamiento si la revisión lo justificaba.
Se identificó una diferencia matemática concreta: promediar las pérdidas
ponderadas de microbatches de 2 no equivale a normalizar por los pesos de todos
los ejemplos del grupo acumulado de hasta 16. La variante conserva los mismos
pesos inversos por clase y divide cada suma parcial por la suma de pesos del
grupo real. Esto corrige la equivalencia del objetivo; su efecto predictivo
todavía debe medirse. La definición de referencia es la
[entropía cruzada ponderada de PyTorch](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html).

Implementación separada en [beto_effective_batch_loss.py](../scripts/beto_effective_batch_loss.py),
sin modificar entrenadores históricos. El [preflight](../outputs/beto-loss-normalization-v1-preflight.json)
pasó 7 comprobaciones: pérdida y gradientes, clases mezcladas y microbatches
homogéneos, grupos incompletos, invariancia al escalado de pesos, orden/RNG y
comparación del entrenamiento CPU completo contra lotes físicos de 16 sin
dropout. No demuestra equivalencia bit a bit con CUDA/AMP/dropout.

Antes de entrenar se declara una única intervención: normalización de pérdida,
manteniendo lr 2e-5, semilla 42, 384 tokens, 2 épocas con horizonte del scheduler de 3,
los mismos 619 TRAIN y los dos grupos por obra. Se compara contra las predicciones
guardadas de la referencia en época 2. Criterio exploratorio: al menos 2 aciertos
adicionales de ideas en cada obra principal, sin caída de F1 macro de siete
clases en ninguna ni de aciertos de ideas dentro del ajuste. Máximo dos nuevas
trayectorias y dos checkpoints; no se hacen predicciones sobre validación,
test, externo 31 o piloto 22. No se selecciona ni publica automáticamente un modelo.

**Resultado: comparación completada; criterio de mejora incumplido.**

| Obra principal excluida del ajuste | Ideas, anterior → corregida | Total correcto, anterior → corregida | F1 macro de siete clases, anterior → corregida |
|---|---|---|---|
| O'Phelan | 0/28 → 0/28 | 34/103 → 33/103 | 0.21880 → 0.21397 |
| Morán | 0/14 → 1/14 | 2/18 → 3/18 | 0.07755 → 0.09048 |

En los datos usados para ajustar, ideas pasa de 34/44 a 36/44 y de 26/61 a
33/61, respectivamente. Sin embargo, los aciertos totales del primer ajuste
bajan de 346/459 a 317/459; en el segundo permanecen en 448/601. Huamanga,
fuente secundaria retenida junto con O'Phelan, pasa de 27/57 a 31/57; sus
3 casos de ideas siguen sin aciertos. El pequeño cambio agregado del grupo
O'Phelan/Huamanga no cumple el criterio de la obra principal.

Se ejecutaron dos trayectorias, dos checkpoints y 1 238 predicciones locales
en 140.21 segundos. Pico CUDA: 2 219 310 592 bytes asignados. La primera
trayectoria realizó 56 actualizaciones frente a 58 de referencia, con dos
omisiones de AMP; la segunda mantuvo 76 y cero omisiones. Las omisiones
son una consecuencia numérica registrada, no otra configuración elegida;
impiden afirmar igualdad de actualizaciones efectivas en la primera ronda.

La [verificación](../artifacts/experiments/beto-loss-normalization-v1/verification.json)
recalculó 14 resúmenes con scikit-learn, alineó las 1 238 predicciones y comprobó
148 entradas protegidas, 18 archivos generados, etiquetas, tokenizadores,
scheduler y decisión. Las 218 filas originales de evaluación y el piloto
adicional permanecen intactos. No se ejecutó inferencia sobre el piloto.

Conclusión limitada: corregir esta normalización no basta para resolver la
clasificación entre obras bajo la receta probada. No demuestra que BETO sea
incapaz ni identifica una causa única. Se conserva la variante experimental
y su evidencia; no se sustituye el modelo servido ni se encadenan más ajustes
automáticos. La revisión histórica sigue señalando unidades que necesitan
contexto antes de poder usarse como etiquetas de referencia fiables.

Evidencia: [protocolo previo](../artifacts/experiments/beto-loss-normalization-v1/protocol.json),
[informe](../artifacts/experiments/beto-loss-normalization-v1/report.json),
[runner](../scripts/compare_beto_loss_normalization.py) y
[pruebas](../scripts/check_beto_effective_batch_loss.py).

## Revisión ciega con agente y piloto adicional de siete clases

La autora autorizó preparar el siguiente bloque y aclaró que no dispone de
revisor humano: pidió crear un agente experto. Se realizó una revisión separada
asistida por IA, con etiquetas iniciales y predicciones ocultas al agente.
Esto atiende la modalidad autorizada, pero no se presenta como historiador
humano, independencia estadística entre revisores ni cumplimiento del objetivo
de revisión humana descrito en la guía. La guía y el corpus v3 no cambiaron.

**Entrenamiento:** el agente revisó los 12 textos exactos del contraste previo,
con identificadores aleatorios y sin etiquetas, rol error/control ni resultados.
Coincidió con la etiqueta existente en 8/12; marcó cinco utilizables y siete
con necesidad de contexto. La concordancia con etiquetas existentes no mide
la exactitud de esas etiquetas. Confirmó el contenido de ideas en Morán
820/826, el liberalismo de Basadre560 y organización en Contreras809.
Para Fonseca49 propuso `no_relevante` por su foco metodológico, coincidiendo
con la propuesta anterior. Marcó577 ambiguo y mantuvo697 como ideas pero con
contexto pendiente. Propuso participación para194/242, ambos cortados, por
beneficiarios sociales y autonomía regional. No se aplicaron esos cambios:
las diferencias deben resolverse sobre unidades completas, no por votación IA.
También señaló contexto pendiente en643 y675. Ninguno de estos textos sirve
como nueva evaluación: todos permanecen asociados a las obras de TRAIN.

**Fuentes nuevas reservadas antes de segmentar:** cuatro artículos de acceso
abierto, con declaración editorial CC BY4.0 archivada, PDF y páginas originales:

- [Choque Mariño2024: visita de Arica1793–1796](https://revistas.pucp.edu.pe/index.php/historica/article/view/31098).
- [Escanilla Huerta2023: impacto de Cádiz1812–1823](https://revistas.pucp.edu.pe/index.php/revistaira/article/view/26980).
- [Guarisco2023: espacio político indígena1821–1822](https://revistas.pucp.edu.pe/index.php/revistaira/article/view/26981).
- [Alvarado Luna2023: deserciones y logística1820–1822](https://revistas.pucp.edu.pe/index.php/revistaira/article/view/26983).

Se seleccionaron 26 candidatos sin consultar predicciones. Los párrafos se
conservaron completos; se recuperaron las continuaciones de Castilla y de dos
unidades de Guarisco entre páginas, separando expresamente notas al pie del
cuerpo. Los tres controles bibliográficos son secuencias de entradas completas.
No se escribió prosa histórica sintética ni se añadieron frases para aclarar
referentes. Se cotejaron visualmente las 27 páginas seleccionadas mediante
PDFium5.13.0, instalado solo en `outputs/independent-review-v1/vendor/`.
La captura PDF remota había fallado; se usaron los PDF locales descargados.

La lectura visual detectó tres rangos numéricos que la unión de guiones de línea
había concatenado:66–67,26–27 y1817–1822. Se restauraron esos guiones y las
separaciones espurias en Reserva, conservar, servicio, sirvió y Tomo I/II/III.
Son siete textos,11 reglas de reemplazo y12 ocurrencias efectivas. Originales,
versiones corregidas y hashes permanecen archivados. El agente comprobó que
estas correcciones no alteraban sus etiquetas ni su juicio de usabilidad.
No se normalizaron nombres, fechas históricas o erratas sustantivas por conjetura.

**Revisión nueva:** primera propuesta IA registrada antes de enviar26textos al
agente en orden mezclado, sin etiquetas iniciales ni cuotas. Segunda revisión
del100% del lote, con acceso al contexto original cuando fue necesario.
Acuerdo inicial22/26 (84.6%), Cohen kappa0.81944. Es acuerdo entre dos procesos
asistidos por IA en una muestra pequeña e intencional; no fiabilidad humana ni
prueba de exactitud, y no se interpreta por clase con estos soportes mínimos.
El agente declaró que, al inspeccionar la estructura de dos archivos de páginas,
vio accidentalmente sus primeras páginas/títulos/resúmenes. No vio claves ni
predicciones, pero no se afirma ceguera perfecta respecto de metadatos de fuente.

Adjudicación: E12 pasa de participación a ideas por evaluar recepción de soberanía;
E19 yE20 pasan de liderazgos a militar por predominio de capitulación, mandos,
reclutamiento y operaciones. Se conserva la propuesta inicial y el motivo de
aceptar la lectura del agente. E08 queda apartado: ideas y agencia indígena
admiten dos lecturas sustantivas. E02/E04/E07 también se apartan por contexto
temporal o referentes ausentes en el texto exacto, aunque el cotejo de páginas
permita aclararlos al lector. No se exige una fecha numérica a toda unidad;
se juzga si la ambigüedad del referente afecta a la clasificación de ese texto.

| Categoría | Ejemplos aceptados |
|---|---:|
| Campañas y conflictos militares | 6 |
| Contexto colonial y antecedentes | 2 |
| Crisis e ideas emancipadoras | 3 |
| Liderazgos, diplomacia y proyectos | 2 |
| No relevante | 4 |
| Organización y consecuencias republicanas | 2 |
| Participación social y regional | 3 |
| **Total** | **22** |

El objetivo orientativo de cuatro por clase no se fuerza: hay carencias y
desbalance explícitos. Los22aceptados tienen125–229 palabras y166–331tokens
con el tokenizador local BETO; todos caben en384sin truncamiento. No se cargó
un clasificador ni se obtuvieron predicciones para medirlo. Las cuatro unidades
apartadas están en un archivo separado, no como octava clase o negativos.

**Límite documental encontrado:** Escanilla cita expresamente enp125 el artículo
de Sala2011 ya utilizado en desarrollo externo y también Guarisco2011. Los tres
artículos RIRA pertenecen al mismo dosier; se conservan como un grupo relacionado.
Alvarado utiliza Miller en otros pasajes de la obra, familia documental presente
en TRAIN, aunque los párrafos de cuerpo seleccionados no lo citan. No se equipara
una cita bibliográfica con copia automática de todo el artículo, ni se afirma
independencia por ausencia de coincidencias textuales. Por eso el archivo queda
congelado como **piloto adicional**, no prueba final plenamente independiente.
La comprobación de los26textos no detectó coincidencias contiguas normalizadas
de8o20palabras con las619filas de train. No se usaron textos ni métricas de
validación/test para elegir ejemplos. Tampoco se releyeron los31textos externos
para seleccionarlos; su relación se identificó en la bibliografía nueva.

**Resultado concreto:** [dataset del piloto](../artifacts/datasets/evaluation-pilot-v2.json),
[informe](../artifacts/reviews/independent-review-v1/report.json),
[adjudicaciones](../artifacts/reviews/independent-review-v1/adjudication.json),
[cuarentenas](../artifacts/reviews/independent-review-v1/quarantine.json),
[revisión de train](../artifacts/reviews/independent-review-v1/training-review.json),
[dependencias](../artifacts/reviews/independent-review-v1/dependency-review.json) y
[verificación](../artifacts/reviews/independent-review-v1/verification.json).
Para lectura directa, [paquete con22textos, fuentes y dictámenes](../outputs/independent-review-v1/revision-piloto.md).
La selección ciega original y las páginas completas permanecen locales.

Comprobaciones:38identidades de revisión,26textos únicos, siete etiquetas con
soporte,22aceptados y4apartados,131entradas protegidas porhash, coincidencias
entre claves y dictámenes y conservación de619train y218validación/test.
La [revisión final del agente](../artifacts/reviews/independent-review-v1/final-peer-check.json)
pasó23comprobaciones sin fallos: reconstruyó correspondencias, conteos, hashes
y acuerdo inicial. La auditoría del cruce contrain y de ausencia de ejecuciones
la contrastó con los certificados disponibles; no la repitió de forma autónoma.
No se entrenó, no se evaluó ningún modelo y no se modificó producción ni Git.
Las tres correcciones previas siguen propuestas, sin aplicación al corpus.

El bloque termina con el piloto y la revisión solicitada. Si se utiliza después,
debe informarse como desarrollo adicional con referencia IA, mostrando soporte,
matriz de confusión y resultados por obra. No sustituye una evaluación final
independiente: siguen faltando amplitud de fuentes, más casos por categoría,
variedad1830–1842 y revisión humana. La fuente de evaluación nunca se recicla
como enriquecimiento de train por haber fallado el modelo. No se inicia otro
experimento automáticamente.

## Cierre de la frontera historiográfica — propuesta terminada

La autora pidió resolver los casos con criterio experto. Se cerraron las tres
decisiones sobre los textos exactos y se preparó un contrato de aplicación con
hash de entrada, identidades y acciones permitidas. Es una decisión metodológica
asistida por IA; no validación humana independiente ni diagnóstico causal de BETO.

**Regla propuesta:** etiquetar la afirmación dominante sobre actores, ideas,
relaciones, estructuras o procesos de 1780–1842. Un autor moderno, una comparación
de interpretaciones o un video pueden desarrollar un argumento histórico válido.
Si domina cómo se escribe la historia, el método del investigador o la moderación,
sin una afirmación histórica sustantiva del periodo, proponer `no_relevante`
para esta tarea. Si cortes o referentes sin atribución impiden decidir, apartar
la unidad incierta en vez de convertirla en negativo. No se exige una fecha
numérica ni un nombre propio por sí solos; se conservan siete clases.

| Índice en snapshot v3, base cero | Decisión propuesta para el texto exacto | Fundamento |
|---|---|---|
| 697 | Cuarentena, conservando original y etiqueta ideas | Pregunta historiográfica con comienzo dependiente y cierre abierto; mezcla con explicación del liberalismo. Sin audio/minutaje local recuperado, no es un positivo ni un negativo seguro |
| 577 | Cuarentena, conservando original y etiqueta ideas | Construcción de precursores y referentes sin atribución suficiente. La acción sobre esta ventana queda cerrada; readmitir exigiría una unidad completa con nuevo hash |
| 49 | Cambiar solo participación a `no_relevante` | Crítica metodológica de relatos y categorías de historiadores. La p.113 de Fonseca confirma que el análisis de participación y el relato de 1820 se anuncian y comienzan después del segmento |

La decisión 49 aplica una aclaración de pertinencia que la guía no explicitaba
por completo; no se presenta como error objetivamente demostrado por una métrica.
El pasaje conserva valor historiográfico y se archiva como contexto académico.
La misma regla conserva ideas en Morán 826/820 y no propone cambiar liderazgos
en 675: este último sí desarrolla relaciones políticas Riva Agüero–San Martín–
Bolívar, aunque se refiera a historias nacionales. No se excluye toda una fuente.
Los cortes de O'Phelan 127/194 no forman parte de estas tres acciones.

**Simulación en memoria, no aplicada:** 617 train, 81 val, 137 test; 14 fuentes.
616 filas de train permanecen idénticas; se apartan dos y se cambia una etiqueta,
sin reemplazar texto. Ideas 75→73, participación 89→88, no_relevante 101→102;
las demás clases no cambian. Supervivientes y evaluación conservan su orden.
El corpus real continúa con 619 train y la guía congelada sigue intacta.

Pasaron ocho comprobaciones separadas de identidad, archivo de originales,
simulación y conservación; se verificaron 134 archivos por hash. Se leyó contexto
de Fonseca en la capa textual del PDF (páginas PDF 8–10), sin adjudicación visual
o de manuscritos. No se recuperó audio ni se supuso continuidad por el orden del
snapshot. Originales, contexto y verificación permanecen locales.

Evidencia: [regla, decisiones y simulación](../artifacts/reviews/beto-historiography-boundary-v1.json)
y [comprobación local](../outputs/beto-historiography-boundary-v1/verification.json).
La propuesta permite revisar exactamente qué se aplicaría a una copia nueva;
no se escribió un dataset candidato ni se aplicaron etiquetas, entrenamientos,
predicciones o cambios en producción/Git.

**Juicio de modelamiento:** estos tres casos justifican saneamiento delimitado,
pero no explican por sí solos los 0/28 y 0/14 de ideas retenidas. El fallo de
transferencia está observado; su mecanismo único sigue sin identificarse.
No hay base nueva para aumentar tokens, repetir épocas o cambiar etiquetas de
Morán. Tampoco se declara incapacidad de BETO, sobreajuste o fallo del optimizador.
Dos cuarentenas y una reclasificación no aíslan una única causa: aplicarlas por
calidad del corpus no demostraría mejora del modelo. Este bloque termina con
las decisiones cerradas y una propuesta verificable; otra aplicación o ensayo
se delimitará antes de ejecutarse.

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
