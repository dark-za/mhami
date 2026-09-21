param(
    [string]$AppRoot = "C:\Program Files\Mhami",
    [string]$Python = "C:\Program Files\Mhami\venv\Scripts\python.exe",
    [string]$Nssm = "C:\Program Files\Mhami\bin\nssm.exe",
    [string]$EnvFile = "C:\ProgramData\Mhami\config\mhami.env",
    [string]$DataRoot = "C:\ProgramData\Mhami"
)

$ErrorActionPreference = "Stop"
$Backend = Join-Path $AppRoot "backend"
if (-not (Test-Path $Python)) {
    throw "Python virtual environment is missing: $Python"
}
if (-not (Test-Path $Nssm)) {
    throw "Signed NSSM wrapper is missing: $Nssm"
}
if (-not (Test-Path $EnvFile)) {
    throw "Create and protect the environment file first: $EnvFile"
}

function Invoke-Nssm {
    param([string[]]$Arguments)
    & $Nssm @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "NSSM failed: $($Arguments -join ' ')"
    }
}

New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
& icacls $DataRoot /inheritance:r /grant:r "SYSTEM:(OI)(CI)F" "Administrators:(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to protect Mhami data directory: $DataRoot"
}
& icacls $EnvFile /inheritance:r /grant:r "SYSTEM:F" "Administrators:F" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to protect Mhami environment file: $EnvFile"
}

$Environment = @(
    "DJANGO_SETTINGS_MODULE=config.settings.prod"
    Get-Content $EnvFile | Where-Object {
        $_ -and -not $_.TrimStart().StartsWith("#") -and $_ -match "^[A-Za-z_][A-Za-z0-9_]*="
    }
)

Push-Location $Backend
try {
    & $Python manage.py upgrade
} finally {
    Pop-Location
}

function Register-MhamiService {
    param([string]$Name, [string[]]$Arguments)
    Invoke-Nssm @("install", $Name, $Python)
    Invoke-Nssm @("set", $Name, "AppDirectory", $Backend)
    Invoke-Nssm @("set", $Name, "AppParameters", ($Arguments -join " "))
    $EnvironmentArguments = @("set", $Name, "AppEnvironmentExtra") + $Environment
    Invoke-Nssm $EnvironmentArguments
    Invoke-Nssm @("set", $Name, "Start", "SERVICE_AUTO_START")
    Invoke-Nssm @("set", $Name, "AppExit", "Default", "Exit")
    Invoke-Nssm @("set", $Name, "ObjectName", "NT SERVICE\$Name", "")
    & icacls $DataRoot /grant:r "NT SERVICE\${Name}:(OI)(CI)M" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to grant data access to virtual service account: $Name"
    }
    & icacls $EnvFile /grant:r "NT SERVICE\${Name}:R" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to grant environment access to virtual service account: $Name"
    }
}

Register-MhamiService "MhamiApi" @("-m", "gunicorn", "config.wsgi:application", "--bind", "127.0.0.1:8000", "--workers", "3")
Register-MhamiService "MhamiWorker" @("-m", "celery", "-A", "config.celery", "worker", "--loglevel=INFO", "--concurrency=2", "--queues=default,media,ai")
Register-MhamiService "MhamiBeat" @("-m", "celery", "-A", "config.celery", "beat", "--loglevel=INFO", "--schedule=C:\ProgramData\Mhami\celerybeat-schedule")

Start-Service MhamiApi, MhamiWorker, MhamiBeat
foreach ($Name in @("MhamiApi", "MhamiWorker", "MhamiBeat")) {
    $Service = Get-CimInstance Win32_Service -Filter "Name='$Name'"
    if ($Service.StartName -ne "NT SERVICE\$Name") {
        throw "Service $Name is not running under its dedicated virtual service account."
    }
}
