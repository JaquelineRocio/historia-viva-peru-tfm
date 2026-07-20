---
language: es
library_name: transformers
pipeline_tag: text-classification
base_model: dccuchile/bert-base-spanish-wwm-cased
tags:
  - beto
  - peruvian-history
  - education
  - experimental
---

# Historia Viva Perú — BETO v1 experimental

Clasificador temático para fragmentos sobre la Independencia y la formación
republicana del Perú (1780–1842). Es un ajuste fino de
[`dccuchile/bert-base-spanish-wwm-cased`](https://huggingface.co/dccuchile/bert-base-spanish-wwm-cased),
entrenado con un snapshot de 814 segmentos revisados y dividido por fuente.

## Uso

```python
from transformers import pipeline

clasificador = pipeline(
    "text-classification",
    model="Jaqueline98/historia-viva-beto-v1",
    tokenizer="Jaqueline98/historia-viva-beto-v1",
)

clasificador("San Martín organizó la expedición libertadora del Perú.")
```

## Resultados

- F1 macro BETO: **0.425**.
- F1 macro TF-IDF + regresión logística: **0.353**.
- Cohen's Kappa del proceso asistido de validación: **0.651**.

El resultado supera el baseline, pero no alcanza el umbral académico definido de
0.70. Se publica como `experimental`; requiere revisión docente y no debe usarse
como autoridad histórica.

## Clases

1. `contexto_colonial_antecedentes`
2. `crisis_ideas_emancipadoras`
3. `participacion_social_regional`
4. `campanias_conflictos_militares`
5. `liderazgos_diplomacia_proyectos`
6. `organizacion_consecuencias_republicanas`
7. `no_relevante`

## Procedencia y limitaciones

El etiquetado fue asistido por IA y no contó con un historiador independiente.
El corpus es pequeño y está limitado a 1780–1842. Las predicciones deben tratarse
como sugerencias editables.

No se declara una licencia propia para estos pesos en esta demostración académica.
El modelo base indica que CC BY 4.0 describe sus intenciones, junto con una
advertencia sobre las licencias del corpus original. Quien reutilice este modelo
debe revisar esa ficha y la procedencia de los datos conforme a su caso de uso.
