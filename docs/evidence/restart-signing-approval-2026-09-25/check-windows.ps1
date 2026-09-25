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
Push-Location $workspace
try {
    & './tmp/restart-runtime/go/bin/go.exe' test -p=2 -mod=readonly -count=1 -v ./internal/recovery ./cmd/fsn-recovery > (Join-Path $PSScriptRoot 'windows-unit.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Unit checks failed' }
    & './tmp/restart-runtime/go/bin/go.exe' test -p=2 -mod=readonly -c -o tmp/signing-approval-windows-tests.exe ./tests/restart > (Join-Path $PSScriptRoot 'windows-build.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Integration build failed' }
    Set-Location tests/restart
    & '../../tmp/signing-approval-windows-tests.exe' '-test.run=^Test(ApprovedOffline(ProcessCuts|Refusals)|OfflineRecovery(ProcessCuts|UncertainCuts|Refusals))$' '-test.v' '-test.timeout=5m' > (Join-Path $PSScriptRoot 'windows-integration.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Integration checks failed' }
    Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-integration.txt') -Tail 8
} finally { Pop-Location }
