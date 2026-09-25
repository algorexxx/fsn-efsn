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
$binary = Join-Path $workspace 'tmp/parent-isolation-windows-tests.exe'
Push-Location $workspace
try {
    & './tmp/restart-runtime/go/bin/go.exe' test -p=2 -mod=readonly -c -o $binary ./tests/restart > (Join-Path $PSScriptRoot 'windows-build.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    Set-Location tests/restart
    & $binary '-test.run=^Test(FinalizeParentIsolatedFromConcurrentImport|HeaderBatchUsesUnstoredParents)$' '-test.v' '-test.count=5' '-test.timeout=1m' > (Join-Path $PSScriptRoot 'windows-after.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Parent isolation regression failed' }
    Get-Content (Join-Path $PSScriptRoot 'windows-after.txt') -Tail 4
} finally { Pop-Location }
