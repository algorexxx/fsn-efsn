$ErrorActionPreference = 'Stop'
$package = 'W:/FusionRestart/restore-rehearsal-2026-09-24/package'
$exitFile = Join-Path $PSScriptRoot 'pack-exit-code.txt'
$statusFile = Join-Path $PSScriptRoot 'pipeline-status.json'
if (Test-Path -LiteralPath $statusFile) { throw 'Pipeline result already exists' }
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'source-manifest-match.json')) { throw 'Source manifest comparison already exists' }
$stage = 'waiting for package'
try {
    while (-not (Test-Path -LiteralPath $exitFile)) {
        if (Test-Path -LiteralPath 'W:/FusionRestart/restore-rehearsal-2026-09-24/STOP-PIPELINE') { throw 'Pipeline stopped before restore' }
        Start-Sleep -Seconds 5
    }
    if ((Get-Content -Raw -LiteralPath $exitFile -Encoding UTF8).Trim() -ne '0') { throw 'Packaging process failed' }
    if (-not (Test-Path -LiteralPath (Join-Path $package 'manifest.json'))) { throw 'Packaging ended without a complete manifest' }
    $stage = 'original source manifest comparison'
    Write-Output $stage
    & py -3 (Join-Path $PSScriptRoot 'verify-source-manifest.py') 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'verify-source-manifest.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Packaged source hashes differ from retained original manifest' }
    $stage = 'full restore and file verification'
    Write-Output $stage
    & (Join-Path $PSScriptRoot 'run-restore.ps1')
    $stage = 'restored index and node service checks'
    Write-Output $stage
    & (Join-Path $PSScriptRoot 'check-restored.ps1')
    $result = [ordered]@{status='passed'; stage=$stage; utc=[DateTime]::UtcNow.ToString('o')}
} catch {
    $result = [ordered]@{status='failed'; stage=$stage; utc=[DateTime]::UtcNow.ToString('o'); error=$_.Exception.Message}
    throw
} finally {
    if ($null -ne $result) {
        [IO.File]::WriteAllText($statusFile, ($result | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
    }
}
