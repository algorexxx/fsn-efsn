$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$binary = Join-Path $workspace 'tmp/full-state-offline-windows-tests.exe'
$env:GOMAXPROCS = '2'
$env:TEMP = Join-Path $workspace 'tmp/offline-signing-temp'
$env:TMP = $env:TEMP
$env:FUSION_RESTART_CHAINDATA = ''
$env:FUSION_RESTART_OFFLINE_FULL_STATE_ROOT = Join-Path $workspace 'tmp/full-state-offline-windows-2026-09-25'
Push-Location (Join-Path $workspace 'tests/restart')
try {
    & $binary '-test.run=^TestOfflineRecovery(ProcessCuts|UncertainCuts|Refusals)$' '-test.v' '-test.timeout=3m' > (Join-Path $PSScriptRoot 'windows-regression.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Small-state regression failed' }
    & $binary '-test.run=^TestFullStateOfflineRecovery$' '-test.v' '-test.timeout=15m' > (Join-Path $PSScriptRoot 'windows-full-state.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Complete-state interruption rehearsal failed' }
    Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-full-state.txt') -Tail 12
} finally { Pop-Location }
