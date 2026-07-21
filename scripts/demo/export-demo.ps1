param(
  [string]$Container = 'tfm-postgres',
  [string]$Database = 'tfm_db',
  [string]$User = 'app_user',
  [string]$Output = 'artifacts/demo/demo-seed.sql.gz',
  [string]$FilesOutput = 'artifacts/demo/files'
)

$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$temporaryDatabase = "hvp_demo_export_$stamp"
$dump = "/tmp/hvp_demo_$stamp.dump"
$sql = "/tmp/hvp_demo_$stamp.sql"
$outputPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $Output))
$rawOutputPath = if ($outputPath.EndsWith('.gz')) { $outputPath.Substring(0, $outputPath.Length - 3) } else { $outputPath }
$filesPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $FilesOutput))
New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($outputPath)) | Out-Null
New-Item -ItemType Directory -Force -Path $filesPath | Out-Null

function Invoke-Docker {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
  & docker @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Docker fallo (codigo $LASTEXITCODE): docker $($Arguments -join ' ')"
  }
}

try {
  Invoke-Docker exec $Container pg_dump -U $User -d $Database -Fc -f $dump
  Invoke-Docker exec $Container createdb -U $User $temporaryDatabase
  Invoke-Docker exec $Container pg_restore -U $User -d $temporaryDatabase $dump

  $sanitize = @'
DELETE FROM tfm_schema.project_memberships;
DELETE FROM tfm_schema.evidence_feedback;
DELETE FROM tfm_schema.audit_events;
DO $$
DECLARE c record;
BEGIN
  FOR c IN
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'tfm_schema'
      AND data_type = 'uuid'
      AND is_nullable = 'YES'
      AND column_name LIKE '%user_id'
  LOOP
    EXECUTE format('UPDATE tfm_schema.%I SET %I = NULL', c.table_name, c.column_name);
  END LOOP;
END $$;
DELETE FROM tfm_schema.users;
UPDATE tfm_schema.resources
SET storage_provider = CASE WHEN storage_path IS NULL THEN storage_provider ELSE 's3' END,
    storage_key = CASE
      WHEN storage_path IS NULL THEN storage_key
      ELSE replace(regexp_replace(storage_path, '^.*storage[\\/]uploads[\\/]', ''), '\\', '/')
    END;
'@
  $sanitize | & docker exec -i $Container psql -v ON_ERROR_STOP=1 -U $User -d $temporaryDatabase
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo sanitizar la base temporal.' }
  Invoke-Docker exec $Container pg_dump -U $User -d $temporaryDatabase --data-only --column-inserts --disable-triggers --schema=tfm_schema -f $sql
  Invoke-Docker cp "${Container}:$sql" $rawOutputPath
  if ($outputPath.EndsWith('.gz')) {
    $inputStream = [IO.File]::OpenRead($rawOutputPath)
    $outputStream = [IO.File]::Create($outputPath)
    try {
      $gzip = [IO.Compression.GZipStream]::new($outputStream, [IO.Compression.CompressionLevel]::Optimal)
      try { $inputStream.CopyTo($gzip) } finally { $gzip.Dispose() }
    } finally {
      $inputStream.Dispose()
      $outputStream.Dispose()
    }
    Remove-Item -LiteralPath $rawOutputPath -Force
  }

  # Archivos de la demo. No se versionan; se suben a Supabase Storage con upload-demo-s3.mjs.
  Invoke-Docker cp "tfm-api:/app/storage/uploads/." $filesPath
  Write-Host "Seed sanitizado y comprimido: $outputPath" -ForegroundColor Green
  Write-Host "Archivos para Supabase Storage: $filesPath" -ForegroundColor Green
} finally {
  & docker exec $Container dropdb -U $User --if-exists $temporaryDatabase 2>$null | Out-Null
  & docker exec $Container sh -c "rm -f $dump $sql" 2>$null | Out-Null
}
