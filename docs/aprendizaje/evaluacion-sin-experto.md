# Evaluación y siguiente paso sin experto

Actualizado: 11 de septiembre de 2026. La autora confirma que no habrá experto para valorar etiquetas. Este documento sustituye las recomendaciones de la guía de aprendizaje y de la plantilla candidata que exigían una referencia humana. Es una propuesta de trabajo; no registra una evaluación nueva ejecutada.

## Evidencia ya disponible

El [informe I/42](../../artifacts/beto-v3/phase-i-family/informe-I42.md) documenta F1 macro sobre V: R2 = 0,532392; H = 0,547008; I = 0,515924. H pasó 2/4 puertas e I 0/4; R2 sigue como referencia experimental. I alcanzó F1 train = 1, pero eso no resolvió la generalización ni identifica por sí solo un problema de etiquetas.

I incluye métricas por clase, matrices, verificación de 444 IDs, recarga del checkpoint, 20 épocas, permutación por ocho familias, bootstrap pareado de 10000 réplicas y sensibilidad al retirar familias. Son resultados exploratorios sobre V, que ya se usó para seleccionar checkpoints; no equivalen a una evaluación final independiente.

La [revisión IA existente](../../artifacts/beto-v3/phase-i-family/ai-review-summary.json) registra 56 casos, 48 consensos y ocho sin resolución; nueve consensos discrepan de V. No son nueve errores confirmados. Es una muestra diagnóstica y no permite estimar la tasa de error de todo el corpus.

## Siguiente paso recomendado

Preparar un piloto de evaluación del procedimiento de etiquetado y de robustez, antes de gastar la última trayectoria libre de desarrollo. Hipótesis a comprobar: el procedimiento candidato mejora la consistencia y la trazabilidad en fronteras temáticas sin aumentar la abstención ni reducir la cobertura de clases. No dar por demostrado que las etiquetas son la causa del rendimiento actual.

1. Reutilizar primero salidas y diagnósticos existentes. Separar dentro de TRAIN ejemplos de desarrollo y de comprobación por familia documental; fijar la selección antes de comparar prompts, con cobertura de las siete clases y varias fuentes. Los 56 casos de V no se usarán para ajustar el prompt. Registrar tamaño y coste del piloto antes de nuevas llamadas: el ledger solo deja una anotación libre de desarrollo; no asumir que revisar unidades existentes es gratis ni reinterpretar las reservas.
2. Comparar el prompt vigente y el candidato sobre los mismos objetivos, con guía, entradas y configuración controladas. Obtener juicios ciegos sin etiquetas previas, predicciones BETO ni respuestas ajenas; preferir modelos distintos cuando estén disponibles. Registrar modelos, versiones, fecha y coste. Sesiones distintas del mismo modelo no garantizan independencia; los modelos diferentes también pueden compartir sesgos. Conservar desacuerdos sin adjudicación forzada.
3. Medir acuerdo porcentual y kappa entre pares, desacuerdos por frontera, estabilidad entre repeticiones, cobertura por clase y abstención. Publicar denominadores y abstenciones por separado: no medir únicamente los casos donde todos aceptaron. Ninguna de estas métricas mide por sí sola exactitud histórica. No usar como juez de un prompt un consenso que incluya la propia salida evaluada.
4. Comprobar automáticamente IDs, hashes, etiquetas permitidas, citas literales y existencia de la regla citada. Una cita presente y una regla existente prueban trazabilidad formal, no que la interpretación sea correcta.
5. Probar invariancia ante espacios y saltos de línea que preserven exactamente las palabras y su orden. Registrar cambios de etiqueta, cobertura y variación de probabilidades si están disponibles, tanto para el anotador como para BETO. No asumir que cambiar nombres, fechas o negar una frase preserve la categoría. Las pruebas de comportamiento complementan las métricas agregadas; véase [CheckList, ACL 2020](https://aclanthology.org/2020.acl-main.442/).
6. Usar las métricas existentes por clase y familia para localizar fallos; conservar el F1 sobre V como desempeño frente a la referencia congelada. Para un experimento futuro, preregistrar intervención, criterios y presupuesto. Mantener S cerrada hasta el cierre previsto. La evaluación en fuentes separadas mide transferencia respecto de sus etiquetas disponibles, no certificación histórica.

Decisión del piloto: avanzar solo si aporta evidencia nueva y trazable de un problema corregible, con resultados favorables en los indicadores fijados previamente y sin ocultar pérdidas de cobertura. Fijar los umbrales antes de obtener nuevas salidas. Si hay mejoras de consistencia pero no evidencia suficiente de corrección, registrarlas como tales; no relabelar automáticamente ni prometer un aumento de F1. Cualquier modificación de TRAIN debe ser una versión nueva. La mejora de BETO necesita su propio contraste posterior.

## Limitación del laboratorio actual

`scripts/aprender_beto.py comparar-etiquetas` exige actualmente `reference_origin: human`. Ese comando corresponde al diseño anterior y todavía no implementa este piloto sin experto. No escribir `human` en una referencia IA para ejecutarlo. El siguiente cambio de software sería incorporar comparación de acuerdo sin gold y procedencia explícita; esta actualización documental no modifica ni ejecuta ese comparador.

Se puede evaluar y avanzar sin experto, delimitando la conclusión a consistencia, trazabilidad, robustez y desempeño respecto de etiquetas disponibles. La corrección histórica experta queda fuera del alcance, no como una tarea pendiente obligatoria.
