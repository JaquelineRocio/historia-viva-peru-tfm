---
language: es
library_name: transformers
pipeline_tag: text-classification
license: mit
tags: [beto, peruvian-history, education, experimental]
---

# Historia Viva Perú — BETO v1 experimental

Clasificador temático para fragmentos sobre Independencia y formación
republicana del Perú (1780–1842). Fue entrenado con un snapshot de 814 segmentos
revisados, dividido por fuente.

## Resultados

- F1 macro BETO: **0.425**.
- F1 macro TF-IDF + regresión logística: **0.353**.
- Cohen's Kappa del proceso asistido de validación: **0.651**.

El resultado supera el baseline, pero no alcanza el umbral académico definido de
0.70. Debe publicarse como `experimental`; requiere revisión docente y no debe
usarse como autoridad histórica.

## Clases

1. `contexto_colonial_antecedentes`
2. `crisis_ideas_emancipadoras`
3. `participacion_social_regional`
4. `campanias_conflictos_militares`
5. `liderazgos_diplomacia_proyectos`
6. `organizacion_consecuencias_republicanas`
7. `no_relevante`

## Limitaciones

El etiquetado fue asistido por IA y no contó con un historiador independiente.
El corpus es pequeño y está limitado a 1780–1842. Las predicciones deben tratarse
como sugerencias editables.
