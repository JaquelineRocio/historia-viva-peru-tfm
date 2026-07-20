param(
  [string]$Container = 'tfm-postgres',
  [string]$Database = 'tfm_db',
  [string]$User = 'app_user',
  [string]$Input = 'artifacts/demo/demo-seed.sql.gz',
  [switch]$ConfirmEmptyDatabase
)

$ErrorActionPreference = 'Stop'
if (-not $ConfirmEmptyDatabase) {
  throw 'La importación reemplaza los datos de demo. Repita con -ConfirmEmptyDatabase.'
}
$inputPath = (Resolve-Path $Input).Path
& docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop no esta disponible.' }

$clear = @'
DO $$
DECLARE names text;
BEGIN
  SELECT string_agg(format('tfm_schema.%I', table_name), ', ')
  INTO names
  FROM information_schema.tables
  WHERE table_schema = 'tfm_schema' AND table_type = 'BASE TABLE' AND table_name <> 'users';
  IF names IS NOT NULL THEN EXECUTE 'TRUNCATE TABLE ' || names || ' RESTART IDENTITY CASCADE'; END IF;
END $$;
'@
$clear | & docker exec -i $Container psql -v ON_ERROR_STOP=1 -U $User -d $Database
if ($LASTEXITCODE -ne 0) { throw 'No se pudo limpiar la base de destino.' }
if ($inputPath.EndsWith('.gz')) {
  $inputStream = [IO.File]::OpenRead($inputPath)
  try {
    $gzip = [IO.Compression.GZipStream]::new($inputStream, [IO.Compression.CompressionMode]::Decompress)
    try {
      $reader = [IO.StreamReader]::new($gzip, [Text.Encoding]::UTF8)
      try { $seed = $reader.ReadToEnd() } finally { $reader.Dispose() }
    } finally { $gzip.Dispose() }
  } finally { $inputStream.Dispose() }
  $seed | & docker exec -i $Container psql -v ON_ERROR_STOP=1 -U $User -d $Database
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo importar el seed comprimido.' }
} else {
  Get-Content -LiteralPath $inputPath -Raw | & docker exec -i $Container psql -v ON_ERROR_STOP=1 -U $User -d $Database
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo importar el seed SQL.' }
}

$membership = @'
INSERT INTO tfm_schema.project_memberships(project_id, user_id, role)
SELECT p.id, u.id,
  CASE WHEN u.role = 'admin' THEN 'admin' ELSE 'collaborator' END
FROM tfm_schema.projects p CROSS JOIN tfm_schema.users u
WHERE p.is_deleted = false AND u.is_deleted = false
ON CONFLICT (project_id, user_id) DO NOTHING;
'@
$membership | & docker exec -i $Container psql -v ON_ERROR_STOP=1 -U $User -d $Database
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron restaurar las membresias.' }
Write-Host 'Demo importada de forma idempotente.' -ForegroundColor Green
