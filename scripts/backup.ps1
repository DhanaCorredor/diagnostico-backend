<#
.SYNOPSIS
    Takes an off-site backup of the production database and checks that it is readable.

.DESCRIPTION
    Neon's free plan can only rewind the last 6 hours, so anything older than that needs a copy
    kept outside Neon. This script writes a compressed pg_dump, verifies it can be listed back,
    and deletes the oldest ones.

    The dump contains patient data: never store it inside this repository, which is public.

.PARAMETER Destination
    Folder where the dumps are written. Keep it outside the repository.

.PARAMETER DatabaseUrl
    Connection string to dump. Defaults to the BACKUP_DATABASE_URL environment variable so the
    credentials never live in a file or in a scheduled task's arguments.

.PARAMETER Keep
    How many dumps to keep. Older ones are deleted.

.EXAMPLE
    $env:BACKUP_DATABASE_URL = "postgresql://user:pass@host.neon.tech/neondb?sslmode=require"
    .\scripts\backup.ps1 -Destination "C:\Backups\diagnostico"
#>
param(
    [Parameter(Mandatory = $true)][string]$Destination,
    [string]$DatabaseUrl = $env:BACKUP_DATABASE_URL,
    [int]$Keep = 14
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
    throw "No connection string. Pass -DatabaseUrl or set BACKUP_DATABASE_URL."
}

$pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
if (-not $pgDump) {
    throw "pg_dump is not on the PATH. Install the PostgreSQL 18 client tools."
}

# pg_dump refuses to read a server newer than itself, and Neon runs PostgreSQL 18.
$version = (& pg_dump --version) -replace '[^0-9.]', ''
if ([int]($version.Split('.')[0]) -lt 18) {
    throw "pg_dump $version is too old for the production server (PostgreSQL 18). Install the 18 client tools."
}

if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$file = Join-Path $Destination "diagnostico-$stamp.dump"

Write-Host "Dumping to $file ..."
& pg_dump --format=custom --no-owner --no-privileges --file=$file $DatabaseUrl
if ($LASTEXITCODE -ne 0) {
    throw "pg_dump failed with exit code $LASTEXITCODE."
}

# A dump that cannot be listed is not a backup: check it before trusting it.
& pg_restore --list $file > $null
if ($LASTEXITCODE -ne 0) {
    Remove-Item $file -Force
    throw "The dump could not be read back and was discarded."
}

$size = [math]::Round((Get-Item $file).Length / 1MB, 2)
Write-Host "Backup OK: $file ($size MB)"

$old = Get-ChildItem -Path $Destination -Filter "diagnostico-*.dump" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Keep
foreach ($f in $old) {
    Remove-Item $f.FullName -Force
    Write-Host "Removed old backup: $($f.Name)"
}
