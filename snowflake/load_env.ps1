# Carrega .env na sessao atual do PowerShell.
# Uso: .\load_env.ps1

$ErrorActionPreference = "Stop"
$envPath = Join-Path $PSScriptRoot ".env"

if (-not (Test-Path $envPath)) {
    Write-Error "Arquivo .env nao encontrado em $envPath. Copie .env.example para .env e preencha."
}

$loaded = 0
Get-Content $envPath -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { return }

    $parts = $line -split "=", 2
    if ($parts.Count -lt 2) { return }

    $key = $parts[0].Trim()
    $value = $parts[1].Trim().Trim('"').Trim("'")

    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
    $loaded++
}

if ($env:SNOWFLAKE_PAT -and -not $env:SNOWFLAKE_PASSWORD) {
    $env:SNOWFLAKE_PASSWORD = $env:SNOWFLAKE_PAT
}

Write-Host "OK: $loaded variaveis carregadas de .env" -ForegroundColor Green
Write-Host ("SNOWFLAKE_ACCOUNT = {0}" -f ($(if ($env:SNOWFLAKE_ACCOUNT) { $env:SNOWFLAKE_ACCOUNT } else { "(vazio)" })))
Write-Host ("SNOWFLAKE_USER = {0}" -f ($(if ($env:SNOWFLAKE_USER) { $env:SNOWFLAKE_USER } else { "(vazio)" })))
Write-Host ("SNOWFLAKE_ROLE = {0}" -f ($(if ($env:SNOWFLAKE_ROLE) { $env:SNOWFLAKE_ROLE } else { "(vazio)" })))
Write-Host ("SNOWFLAKE_PAT = {0}" -f ($(if ($env:SNOWFLAKE_PAT) { "(definido)" } else { "(vazio)" })))

$profilesDir = Join-Path $PSScriptRoot "dbt_openfootball"
if (Test-Path $profilesDir) {
    $env:DBT_PROFILES_DIR = (Resolve-Path $profilesDir).Path
    Write-Host ("DBT_PROFILES_DIR = {0}" -f $env:DBT_PROFILES_DIR)
}
