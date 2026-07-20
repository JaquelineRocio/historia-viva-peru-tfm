# Modal paso a paso — servicio ML permanente de la demo

Modal sustituye a Hugging Face Spaces para ejecutar FastAPI y BETO. El plan
Starter cuesta USD 0 e incluye USD 30 mensuales de cómputo. El contenedor escala
a cero cuando no recibe solicitudes, por lo que el evaluador puede abrir una URL
estable sin depender del equipo de la autora.

## 1. Crear la cuenta

1. Abra <https://modal.com> y cree una cuenta Starter.
2. No seleccione Team ni añada contenedores siempre activos.
3. Compruebe en Billing que el plan sea `Starter — $0`.

## 2. Instalar y autenticar la CLI

Desde PowerShell:

```powershell
python -m pip install --upgrade modal
python -m modal setup
```

El segundo comando abre el navegador para autorizar este equipo.

## 3. Crear el secreto interno

Genere una cadena aleatoria y guárdela; Render utilizará el mismo valor:

```powershell
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$mlToken = [Convert]::ToBase64String($bytes)
$mlToken
```

En Modal abra **Secrets** → **Create secret** → **Custom**:

```text
Secret name: historia-viva-ml
ML_INTERNAL_TOKEN: valor generado
```

No comparta ni publique este valor.

Después cree un **Proxy Token** desde el panel de Modal:

1. Abra <https://modal.com/settings/proxy-auth-tokens>.
2. Pulse **Create Proxy Token**.
3. Guarde los dos valores mostrados:

```text
MODAL_PROXY_TOKEN_ID=wk-...
MODAL_PROXY_TOKEN_SECRET=ws-...
```

Esta autenticación rechaza solicitudes anónimas antes de encender un contenedor y
protege el crédito gratuito.

## 4. Desplegar

Desde la raíz del proyecto:

```powershell
python -m modal deploy apps/ml/modal_app.py
```

El primer build instala las dependencias e incorpora
`Jaqueline98/historia-viva-beto-v1` a la imagen. Puede tardar varios minutos.
El comando termina mostrando una URL HTTPS estable `modal.run`.

## 5. Verificar

Pruebe con PowerShell, usando el Proxy Token:

```powershell
$headers = @{
  "Modal-Key" = "wk-..."
  "Modal-Secret" = "ws-..."
}
Invoke-RestMethod -Uri "https://URL-DE-MODAL/health" -Headers $headers
```

En Windows PowerShell 5.1, convierta expresamente el JSON a UTF-8 antes de
probar una inferencia. Esto evita errores al enviar tildes o la letra `ñ`:

```powershell
$headers["X-Internal-Token"] = $mlToken
$json = @{
  texts = @(
    "San Martín organizó la expedición libertadora para asegurar la independencia del Perú."
  )
} | ConvertTo-Json -Compress
$bodyUtf8 = [System.Text.Encoding]::UTF8.GetBytes($json)

Invoke-RestMethod `
  -Uri "https://URL-DE-MODAL/infer" `
  -Method Post `
  -Headers $headers `
  -ContentType "application/json; charset=utf-8" `
  -Body $bodyUtf8
```

Durante el primer arranque BETO puede aparecer como `loading`. Después debe verse:

```text
components.beto.ready = true
components.beto.status = ready
```

Guarde para Render:

```text
ML_SERVICE_URL=https://URL-DE-MODAL
ML_INTERNAL_TOKEN=el mismo secreto
MODAL_PROXY_TOKEN_ID=wk-...
MODAL_PROXY_TOKEN_SECRET=ws-...
```

## 6. Límites de coste

La función solicita 2 CPU, 8 GB de RAM, un máximo de un contenedor y escala a
cero después de dos minutos sin actividad. No configure `min_containers` por
encima de cero. Revise Usage en Modal antes y después de la defensa.

La URL permanece disponible cuando no hay contenedores; la primera solicitud
después de un periodo inactivo tendrá un arranque en frío. Los vídeos sin
subtítulos pueden tardar más por Whisper y deben evitarse en la prueba pública.

## Referencias oficiales

- [Precios de Modal](https://modal.com/pricing)
- [Aplicaciones FastAPI/ASGI](https://modal.com/docs/guide/webhooks)
- [Pesos de Hugging Face](https://modal.com/docs/guide/model-weights)
- [CPU y memoria](https://modal.com/docs/guide/resources)
- [Escalado a cero](https://modal.com/docs/guide/scale)
