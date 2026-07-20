# Hugging Face paso a paso — Historia Viva Perú

## Parte A. Repositorio del modelo BETO

### 1. Crear el modelo

1. Inicie sesión en Hugging Face.
2. Abra <https://huggingface.co/new>.
3. En **Owner**, seleccione su usuario.
4. En **Model name**, escriba `historia-viva-beto-v1`.
5. Seleccione **Public** para que el servicio ML pueda descargarlo sin token.
6. No seleccione una licencia si todavía no ha decidido una.
7. Pulse **Create model**.

El identificador tendrá esta forma:

```text
Jaqueline98/historia-viva-beto-v1
```

### 2. Preparar los archivos

El modelo ya está descomprimido en:

```text
apps/ml/storage/models/beto-v1-gold-source-aware
```

No suba `modelo_vN.zip`. Los archivos deben quedar en la raíz del repositorio de
Hugging Face.

Suba:

```text
config.json
experiment.json
labels.json
metrics.json
model.safetensors
special_tokens_map.json
tokenizer.json
tokenizer_config.json
vocab.txt
README.md
```

Use como `README.md` la ficha `deploy/huggingface-model/README.md`.
`training_args.bin` no se necesita para inferencia y puede omitirse.

### 3. Subir desde la web

1. Abra **Files and versions** en el modelo recién creado.
2. Pulse **+ Contribute** (arriba a la derecha) → **Upload files**.
   Si el menú no muestra la opción, abra directamente
   `https://huggingface.co/Jaqueline98/historia-viva-beto-v1/upload/main`.
3. Arrastre los nueve archivos indicados del modelo y el `README.md`.
4. Escriba el mensaje `Publicar BETO v1 experimental`.
5. Pulse **Commit changes** y espere a que termine `model.safetensors` (419 MB).

La interfaz web admite archivos grandes. Si la conexión se interrumpe, use la CLI:

```powershell
python -m pip install --upgrade huggingface_hub
hf auth login
hf upload Jaqueline98/historia-viva-beto-v1 .\apps\ml\storage\models\beto-v1-gold-source-aware . --repo-type model
hf upload Jaqueline98/historia-viva-beto-v1 .\deploy\huggingface-model\README.md README.md --repo-type model
```

El token se crea en <https://huggingface.co/settings/tokens>. Use un token con
permiso de escritura, introdúzcalo solo en su terminal y nunca lo comparta ni lo
guarde en GitHub.

### 4. Verificar

En **Files and versions**, `config.json` y `model.safetensors` deben verse en el
primer nivel. Después ejecute en Colab:

```python
!pip -q install transformers safetensors torch

from transformers import AutoModelForSequenceClassification, AutoTokenizer

repo = "Jaqueline98/historia-viva-beto-v1"
tokenizer = AutoTokenizer.from_pretrained(repo)
model = AutoModelForSequenceClassification.from_pretrained(repo)

print(model.config.id2label)
print("Modelo disponible:", model is not None)
```

La salida correcta muestra las siete etiquetas y `Modelo disponible: True`.

Guarde estos valores:

```text
URL_MODELO=https://huggingface.co/Jaqueline98/historia-viva-beto-v1
ML_DEFAULT_MODEL_REPO=Jaqueline98/historia-viva-beto-v1
```

## Parte B. Servicio ML con Modal

Desde 2026, Hugging Face exige un plan pagado para crear Spaces con Gradio o
Docker. Solo los Spaces estáticos permanecen gratuitos y no pueden ejecutar este
servicio FastAPI/PyTorch. Por ello, el modelo permanece en Hub, pero el servicio
ML de la demostración se despliega en Modal Starter mediante
`apps/ml/modal_app.py`.

1. Cree una cuenta Modal Starter.
2. Cree el secreto `historia-viva-ml` con `ML_INTERNAL_TOKEN`.
3. Cree un Proxy Token de Modal.
4. Ejecute `python -m modal deploy apps/ml/modal_app.py`.
5. Use la URL HTTPS resultante como `ML_SERVICE_URL` en Render.

El plan Starter cuesta USD 0 e incluye crédito mensual. La función escala a cero;
la URL permanece estable y la primera solicitud puede tener un arranque en frío.
Consulte `docs/modal-paso-a-paso.md`.

## Referencias oficiales

- [Subir modelos](https://huggingface.co/docs/hub/models-uploading)
- [Repositorios y archivos grandes](https://huggingface.co/docs/hub/repositories-getting-started)
- [`hf upload`](https://huggingface.co/docs/huggingface_hub/guides/upload)
- [Condiciones actuales de Spaces](https://huggingface.co/spaces/launch)
- [Precios de Modal](https://modal.com/pricing)
- [Web Functions de Modal](https://modal.com/docs/guide/webhooks)
