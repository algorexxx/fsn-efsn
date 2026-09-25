$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$report = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'source-manifest-match.json') -Encoding UTF8 | ConvertFrom-Json
$instance = 'W:/FusionRestart/restore-rehearsal-2026-09-24/restored-node/efsn'
$marker = Get-Content -Raw -LiteralPath (Join-Path $instance 'restored.json') -Encoding UTF8 | ConvertFrom-Json
if ($marker.manifest_sha256 -ne $report.manifest_sha256) { throw 'Restore marker differs from verified package' }
$env:GOMAXPROCS = '2'
$env:FUSION_RESTART_FULL_AUDIT = '1'
$env:FUSION_RESTART_CHAINDATA = Join-Path $instance 'chaindata'
$env:FUSION_RESTART_SNAPSHOT_INDEX_OUTPUT = Join-Path $PSScriptRoot 'restored-index-inventory.json'
$env:FUSION_RESTART_RESTORED_NODE = $instance
$env:FUSION_RESTART_RESTORED_MANIFEST = $report.manifest_sha256
$binary = Join-Path $workspace 'tmp/snapshot-restore-windows-tests.exe'
Push-Location (Join-Path $workspace 'tests/restart')
try {
    & $binary '-test.run=^TestSnapshotIndexInventory$' '-test.v' '-test.timeout=15m' 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'restored-index-inventory.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Restored index inspection failed' }
    $original = Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'source-index-inventory.json')
    $restored = Get-FileHash -LiteralPath $env:FUSION_RESTART_SNAPSHOT_INDEX_OUTPUT
    if ($original.Hash -ne $restored.Hash) { throw 'Restored index report differs from source' }
    & $binary '-test.run=^TestRestoredSnapshotService$' '-test.v' '-test.timeout=15m' 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'restored-service.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Restored node service check failed' }
    & $binary '-test.run=^TestRestoredSnapshotService$' '-test.v' '-test.timeout=15m' 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'restored-service-reopen.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Restored node fresh-process reopen failed' }
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'restored-check-exit-code.txt'), '0', [Text.UTF8Encoding]::new($false))
} finally {
    Pop-Location
}
