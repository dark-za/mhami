param(
    [string]$AppRoot = "C:\Program Files\Mhami",
    [switch]$RemoveData
)

$ErrorActionPreference = "Stop"
$CurrentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object Security.Principal.WindowsPrincipal($CurrentIdentity)
if (-not $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run the Mhami uninstaller from an elevated PowerShell session."
}
if (-not $RemoveData) {
    throw "Refusing to remove application data. Re-run with -RemoveData after taking a backup."
}

@("MhamiApi", "MhamiWorker", "MhamiBeat") | ForEach-Object {
    Stop-Service $_ -ErrorAction SilentlyContinue
    & (Join-Path $AppRoot "bin\nssm.exe") remove $_ confirm
}
Remove-Item -LiteralPath $AppRoot -Recurse -Force
Remove-Item -LiteralPath "C:\ProgramData\Mhami" -Recurse -Force
