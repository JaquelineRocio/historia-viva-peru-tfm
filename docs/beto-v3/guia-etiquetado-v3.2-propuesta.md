# Guía de etiquetado v3.2 — propuesta mínima

Estado: **propuesta para aprobación; no vigente ni aplicada**. Fecha: 2026-09-11.

Esta versión es la composición de la [guía v3.1](guia-etiquetado-v3.1.md), SHA256 `1e4e108ae3e3621ee33db071e4a2f4766bbec20da4ec875b1d677199f17fe23c`, y las cinco enmiendas siguientes. No es una guía autónoma: se entregarán ambos documentos completos al anotador. Las enmiendas prevalecen exclusivamente en los puntos enumerados. Las afirmaciones heredadas «no introduce estados nuevos» describen v3.1: v3.2 sí propone el estado administrativo `unresolved`, de forma explícita.

Se conservan las siete clases, el alcance histórico, R0, las restantes fronteras y el contrato de **solo texto objetivo**. No se entregan contexto adyacente, etiquetas anteriores, predicciones BETO ni casos de la auditoría expuesta. La referencia sigue siendo asistida por IA, nunca gold experto. Ninguna disposición autoriza cambios de datos, entrenamiento o acceso a V/S.

## G32-1. Anuncio temático frente a explicación histórica (precisa R0/R7)

Identificar qué afirma el objetivo, no únicamente de qué tema habla. Un anuncio de lo que un artículo estudiará, su estructura o sus objetivos, sin desarrollo histórico sustantivo, corresponde a R7 aunque mencione personajes, conflictos o instituciones pertinentes.

Hay desarrollo sustantivo cuando el objetivo formula una afirmación histórica concreta sobre acciones, relaciones, condiciones, posiciones, prácticas o consecuencias. No se exige que toda descripción pruebe causalidad. Si un párrafo combina presentación del estudio con una afirmación histórica desarrollada, aplicar R0 al argumento: no descartarlo por contener «este artículo» ni por citar historiadores.

Registrar una cita literal que permita distinguir anuncio de desarrollo y explicar su función. La presencia de nombres, fechas y temas no satisface ese requisito por sí sola. R7 también conserva los demás supuestos de alcance de v3.1; relevancia del artículo completo no equivale a pertinencia del objetivo aislado.

## G32-2. Evidencia positiva de R2

Asignar `crisis_ideas_emancipadoras` solo cuando el argumento dominante desarrolla al menos uno de estos objetos:

- Una crisis o disputa de legitimidad o soberanía: identificar qué autoridad, fundamento u orden se cuestiona o pretende legitimar.
- El contenido de una idea política pertinente al alcance de la tarea.
- La circulación, apropiación o uso de una idea identificable: indicar qué idea y qué proceso de circulación, apropiación o uso explica el objetivo. No es obligatorio que cite literalmente una doctrina, pero sí que permita identificarla sin importarla de otra fuente.

Registrar cita literal y explicar cómo sostiene el objeto elegido. «Prensa», «republicano», «constitución» o una fecha anterior a la instalación de una institución no bastan aisladamente. Tampoco se obtiene R2 por excluir R5. Se conservan F5.b/F5.c: si domina la agencia de un grupo o la competencia de proyectos concretos atribuidos a personas, evaluar R6/R4 con sus propios requisitos positivos.

## G32-3. Preparación y funcionamiento efectivo (precisa R5/F2)

En esta frontera, «implantación» en R5 significa un acto de puesta en ejercicio o implementación efectivamente realizado que el objetivo desarrolla: por ejemplo, constituir e instalar un órgano, ejercer una atribución o aplicar una norma. No exige una institución consolidada ni exitosa; un acto efectivo de instalación puede ser objeto de R5. Debe identificarse qué acto ocurrió y qué explica el objetivo sobre él, no solo una fecha o una institución nombrada.

Preparar el ambiente, esperar una instalación, promover su futura creación o anunciar su próximo funcionamiento no demuestra ese ejercicio. No etiquetar R5 solo porque la conclusión mencione un resultado institucional futuro. Tampoco excluir toda acción previa: una institución que ya actúa puede adoptar medidas preparatorias; si el argumento desarrolla el ejercicio de sus atribuciones, evaluar R5 sobre esa actuación efectiva.

El tiempo verbal o la cronología aislados no deciden. Identificar el objeto y la acción desarrollada. Si hay disputa o ideas con evidencia positiva, evaluar R2; si hay proyectos o conducción política, R4; si domina otra clase, aplicar su regla. Si ninguna asignación única se sostiene, aplicar G32-4. Esto sustituye la lectura automática de F2 «antes de instalarse → R2 / después → R5» y conserva su distinción entre legitimidad y funcionamiento.

## G32-4. Pertinencia sin asignación única

El estado de revisión y la clase temática son campos distintos:

| Estado | Condición | `label` | Tratamiento |
|---|---|---|---|
| `accepted` | Una clase domina con evidencia suficiente; incluye R7 sustentada por su regla | Una de las siete clases | Referencia candidata; no admisión automática |
| `ambiguous` | Dos clases tienen desarrollo comparable y cumplen las condiciones conjuntas de v3.1 sin prioridad resoluble | `null` | Registrar al menos dos clases sustentadas, sus evidencias y la contradicción |
| `unresolved` **nuevo** | Hay desarrollo histórico pertinente y extracción utilizable, pero no se sostiene una asignación única ni se cumplen los requisitos de `ambiguous` | `null` | Registrar argumento pertinente, requisitos faltantes y motivo |
| `pending_extraction` | Defecto concreto de extracción impide decidir | `null` | Identificar defecto; no atribuirlo a la mera falta de contexto |

Motivos de `unresolved`: `insufficient_positive_evidence` (ninguna clase tiene evidencia positiva suficiente para dominar) o `rule_boundary_unresolved` (hay candidatos plausibles pero las reglas no resuelven su encaje; indicar exactamente dónde). No usarlo por dificultad genérica, preferencia personal ni simple desacuerdo entre anotadores. No simular dos temas igualmente desarrollados para producir `ambiguous`.

En `ambiguous` y `unresolved`, `alternative=null`: no hay etiqueta principal respecto de la cual definir una alternativa. Registrar las hipótesis en `considered_classes`, con evidencia a favor y requisito faltante; no tratarlas como etiquetas adjudicadas. Para `ambiguous` deben existir al menos dos clases positivamente sustentadas.

Estos estados permanecen fuera de entrenamiento y F1 de referencia única. Publicar sus recuentos sobre **todos** los objetivos, por fuente y motivo. Una mayor abstención no constituye mejora automática. La diferencia con R7 es positiva: existe argumento histórico pertinente, que debe citarse. Una carencia de evidencia discriminante no elimina ese argumento.

## G32-5. Alternativa subordinada y registro

Resolver primero estado y etiqueta principal. Para `accepted`, registrar `alternative` solo si otra clase histórica tiene un tema secundario desarrollado y evidencia positiva propia; explicar por qué queda subordinada bajo R0. No usar alternativas para palabras incidentales, candidatos descartados, incertidumbre genérica ni R7 frente a contenido pertinente. Si no existe ese segundo desarrollo, usar `null`. En R7, `alternative=null`.

Evaluar principal y alternativa por separado. Una alternativa cambiante no se contabiliza como cambio de principal, aunque sí como inestabilidad del registro secundario. Esta separación es prospectiva: no cambia el resultado de ninguna puerta anterior.

Contrato adicional de registro: `status`, `label`, `alternative`, `main_claim`, `evidence` (lista de citas con offsets base cero y fin excluido), `rule_ids`, `justification`, `alternative_evidence`, `alternative_reason`, `unresolved_reason`, `considered_classes`, `extraction_issue`. Los campos inaplicables serán `null` o listas vacías según el esquema que se congele; nunca se rellenarán inventando evidencia. Cada hipótesis de `considered_classes` tendrá `label`, `support` y `missing_requirement`. ID opaco obligatorio; familia, hash de objetivo, modelo y versión de guía se añaden desde el manifiesto privado, sin inferirlos del texto.

No se incluyen los cuatro casos expuestos como ejemplos ni como validación. La implementación futura requiere adaptar expresamente el validador al nuevo estado; no falsificar procedencia humana ni pasar esta versión por un ejecutor que solo entiende el contrato anterior.
