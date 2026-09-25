$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$env:CGO_ENABLED = '0'
$env:GOMAXPROCS = '2'
$env:GOTOOLCHAIN = 'local'
$env:GOPROXY = 'off'
$env:GOCACHE = Join-Path $workspace 'tmp/restart-runtime/gocache'
$env:GOPATH = Join-Path $workspace 'tmp/restart-runtime/gopath'
$env:GOTMPDIR = Join-Path $workspace 'tmp/restart-runtime/gotmp'
$env:TEMP = Join-Path $workspace 'tmp/offline-signing-temp'
$env:TMP = $env:TEMP
$env:FUSION_RESTART_CHAINDATA = ''
$env:FUSION_RESTART_OFFLINE_FULL_STATE_ROOT = ''
$env:FUSION_RESTART_OPERATOR_FULL_STATE_ROOT = Join-Path $workspace 'tmp/full-state-operator-windows-2026-09-25'
$env:FUSION_RECOVERY_OPERATOR = Join-Path $workspace 'tmp/fsn-recovery-operator.exe'
$binary = Join-Path $workspace 'tmp/full-state-operator-windows-tests.exe'
if ((Get-FileHash -LiteralPath $env:FUSION_RECOVERY_OPERATOR).Hash.ToLowerInvariant() -ne '5272d5eb4dd0c490abb78d22af7e44781870329c43e1c0913533cabde2b1e4d3') { throw 'Reviewed operator binary changed' }
Push-Location $workspace
try {
    & './tmp/restart-runtime/go/bin/go.exe' test -p=2 -mod=readonly -c -o $binary ./tests/restart > (Join-Path $PSScriptRoot 'windows-build.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Integration build failed' }
    Set-Location tests/restart
    & $binary '-test.run=^TestRecoveryOperatorCLI$' '-test.v' '-test.timeout=3m' > (Join-Path $PSScriptRoot 'windows-regression.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Small-state command regression failed' }
    & $binary '-test.run=^TestFullStateRecoveryOperator$' '-test.v' '-test.timeout=10m' > (Join-Path $PSScriptRoot 'windows-full-state.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Complete-state operator rehearsal failed' }
    Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-full-state.txt') -Tail 12
} finally { Pop-Location }
