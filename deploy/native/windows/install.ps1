param(
    [string]$AppRoot = "C:\Program Files\Mhami",
    [ValidateSet("central", "standalone")]
    [string]$Mode = "standalone",
    [string]$Hostname = "localhost"
)

$ErrorActionPreference = "Stop"
$CurrentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object Security.Principal.WindowsPrincipal($CurrentIdentity)
if (-not $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run the Mhami installer from an elevated PowerShell session."
}
$Python = Join-Path $AppRoot "venv\Scripts\python.exe"
$Installer = Join-Path $AppRoot "deploy\native\installer.py"
$DataRoot = "C:\ProgramData\Mhami"
$ConfigRoot = Join-Path $DataRoot "config"
$EnvFile = Join-Path $ConfigRoot "mhami.env"

New-Item -ItemType Directory -Force -Path $ConfigRoot | Out-Null

if (-not (Test-Path $Python)) {
    throw "Create the Python 3.13 virtual environment before running this script."
}
if (-not (Test-Path $Installer)) {
    throw "Native installer is missing: $Installer"
}

& $Python $Installer --mode $Mode --hostname $Hostname --env-file $EnvFile --data-root $DataRoot
if ($LASTEXITCODE -ne 0) {
    throw "Environment preparation failed."
}

Push-Location (Join-Path $AppRoot "backend")
try {
    & $Python manage.py upgrade
    if ($LASTEXITCODE -ne 0) {
        throw "Django upgrade failed."
    }
} finally {
    Pop-Location
}

& (Join-Path $AppRoot "deploy\native\windows\register-services.ps1") `
    -AppRoot $AppRoot -Python $Python -EnvFile $EnvFile -DataRoot $DataRoot
