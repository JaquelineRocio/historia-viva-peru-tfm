param(
  [Parameter(Mandatory = $true)][string]$ApiUrl,
  [string]$Username = 'docente',
  [string]$Password = 'tfm2026'
)

$ErrorActionPreference = 'Stop'
$base = $ApiUrl.TrimEnd('/')

function Assert-True([bool]$Condition, [string]$Message) {
  if (-not $Condition) { throw $Message }
  Write-Host "OK  $Message" -ForegroundColor Green
}

$health = Invoke-RestMethod "$base/api/health"
Assert-True ($null -ne $health) 'API responde a /health'

try {
  Invoke-RestMethod "$base/api/auth/login" -Method Post -ContentType 'application/json' -Body '{"username":"docente","password":"incorrecta"}'
  throw 'El login incorrecto fue aceptado'
} catch {
  Assert-True ($_.Exception.Response.StatusCode.value__ -in 401, 429) 'Login incorrecto rechazado'
}

$login = Invoke-RestMethod "$base/api/auth/login" -Method Post -ContentType 'application/json' -Body (@{ username=$Username; password=$Password } | ConvertTo-Json)
Assert-True (![string]::IsNullOrWhiteSpace($login.accessToken)) 'Login de demostración correcto'
$headers = @{ Authorization = "Bearer $($login.accessToken)" }
$projects = Invoke-RestMethod "$base/api/projects" -Headers $headers
Assert-True ($projects.Count -gt 0) 'Existe al menos un proyecto accesible'

$projectId = $projects[0].id
$body = @{ query='¿Qué relación tuvo Apolo 11 con la Independencia peruana?' } | ConvertTo-Json
$utf8Body = [Text.Encoding]::UTF8.GetBytes($body)
$answer = Invoke-RestMethod "$base/api/projects/$projectId/assistant/query" -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body $utf8Body
Assert-True (
  $answer.mode -eq 'abstained' -and
  $answer.evidence.Count -eq 0 -and
  $answer.answer -eq 'No encuentro respaldo suficiente en las fuentes disponibles.'
) 'Apolo 11 produce abstención sin evidencias'

Write-Host 'Smoke test completado.' -ForegroundColor Cyan
