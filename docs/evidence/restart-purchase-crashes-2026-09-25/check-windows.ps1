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
$env:FUSION_PURCHASE_CRASH_REHEARSAL = '1'
$binary = Join-Path $workspace 'tmp/purchase-crash-windows-tests.exe'
Push-Location $workspace
try {
    & './tmp/restart-runtime/go/bin/go.exe' test -p=2 -mod=readonly -c -o $binary ./tests/restart > (Join-Path $PSScriptRoot 'windows-build.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Integration build failed' }
    Set-Location tests/restart
    & $binary '-test.run=^TestAutomaticPurchaseCrashBoundaries$' '-test.v' '-test.timeout=10m' > (Join-Path $PSScriptRoot 'windows-crashes.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Purchase interruption checks failed' }
    Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-crashes.txt') -Tail 19
} finally { Pop-Location }
