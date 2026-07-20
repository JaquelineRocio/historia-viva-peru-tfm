---
title: Historia Viva Perú ML
emoji: 📚
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
---

# Historia Viva Perú — servicio ML

Space Docker para segmentación, embeddings, NER e inferencia BETO. Configure los
secretos `ML_INTERNAL_TOKEN` y `ML_DEFAULT_MODEL_REPO`. El modelo se descarga
desde Hugging Face Hub al arrancar; `/health` informa el estado de BETO,
embeddings y NER.

Este componente es experimental. BETO v1 obtuvo F1 macro 0.425 y no se presenta
como un modelo robusto ni recomendado.
