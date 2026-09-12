---
language: es
library_name: transformers
pipeline_tag: text-classification
base_model: dccuchile/bert-base-spanish-wwm-cased
tags:
  - beto
  - peruvian-history
  - experimental
---

# Historia Viva Perú — BETO R2, semilla 42

Clasificador temático experimental de siete categorías para fragmentos de historia
del Perú. Checkpoint de la época 8 de la receta R2, semilla 42; BETO base en revisión
`c4d86612f51b4f46759c8390d1798c2febe71b93`. Entrenamiento registrado: 1016 textos.

F1 macro registrado en V (444 fragmentos): **0,532392**. Es desempeño frente a la
referencia disponible; V se utilizó durante el desarrollo y no es una prueba final
independiente. No equivale a porcentaje de respuestas correctas ni a corrección
histórica certificada. S permanece cerrada.

El etiquetado fue asistido por IA, sin validación de un experto independiente.
El acuerdo IA no constituye gold experto. Las predicciones son sugerencias
experimentales, con limitaciones de generalización por fuente y familia documental.

## Inferencia

Usar truncamiento a **384 tokens**, incluido el contenido especial del tokenizer.
El orden de salida está en `config.json` y en `labels.json` (`id2label`):

1. `campanias_conflictos_militares`
2. `contexto_colonial_antecedentes`
3. `crisis_ideas_emancipadoras`
4. `liderazgos_diplomacia_proyectos`
5. `no_relevante`
6. `organizacion_consecuencias_republicanas`
7. `participacion_social_regional`

El paquete conserva los pesos y tokenizer originales. Solo adapta los metadatos
`labels.json` al contrato del servicio. Su comprobación con textos sintéticos
verifica paridad de empaquetado, no mejora de F1.

No se añade una licencia propia para los pesos. Se conserva como referencia la
[ficha del modelo base](https://huggingface.co/dccuchile/bert-base-spanish-wwm-cased)
y sus condiciones; esta entrega no redistribuye los corpus de trabajo.
