# Protocolo reproducible del experimento

## Corpus y partición

- Periodo: 1780–1842.
- Tamaño objetivo: 700–900 segmentos gold, al menos 100 por clase.
- Diversidad: 8–12 fuentes, combinando PDF y YouTube.
- La licencia es opcional; título, autor y procedencia se registran cuando se conocen.
- Agrupar por fuente: una fuente completa pertenece solo a `train`, `validation` o `test`.
- Calcular hashes y similitud para retirar duplicados; ventanas solapadas nunca se separan entre splits.

## Experimentos

1. Baseline mayoritario.
2. TF-IDF de palabras y bigramas con regresión logística y semilla fija.
3. BETO v1 sobre el snapshot gold congelado.
4. BETO v2 con correcciones y ejemplos difíciles seleccionados mediante active learning.

Cada ejecución debe registrar snapshot, versión de taxonomía, semilla, dependencias, hiperparámetros, artefacto y fecha. Se reportan F1 macro y weighted, precision/recall/F1 por clase, matriz de confusión, intervalos de confianza por bootstrap y errores representativos. Los resultados de PDF y YouTube se presentan también por separado.

## Criterios para recomendar

El modelo debe superar TF-IDF, alcanzar F1 macro ≥ 0.70 y ninguna clase puede tener F1 < 0.50. La aplicación conserva otros modelos como `experimental`; únicamente un administrador puede activarlos explícitamente.

## Evaluación de recuperación

Preparar preguntas con respuesta y preguntas negativas. Medir Recall@5 (objetivo ≥ 0.80), abstención correcta (objetivo ≥ 90%) y validez de citas. La respuesta obligatoria sin evidencia es: “No encuentro respaldo suficiente en las fuentes disponibles”.

## Evidencia para la memoria

Exportar la distribución del corpus, asignación de fuentes por split, acuerdo entre anotadores, tablas de métricas, matrices de confusión, ejemplos de error y resultados de las pruebas con 5–8 docentes. No declarar como alcanzada una métrica hasta ejecutar y conservar su resultado.

