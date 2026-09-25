param([string]$Overlay = '', [string]$Label = 'current')
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
$binary = Join-Path $workspace "tmp/cold-headers-$Label-windows-tests.exe"
$arguments = @('test', '-p=2', '-mod=readonly', '-c', '-o', $binary)
if ($Overlay) { $arguments += "-overlay=$Overlay" }
$arguments += './tests/restart'
Push-Location $workspace
try {
    & './tmp/restart-runtime/go/bin/go.exe' @arguments > (Join-Path $PSScriptRoot "windows-$Label-build.txt") 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
    Set-Location tests/restart
    & $binary '-test.run=^TestColdHeaderValidationBoundaries$' '-test.v' '-test.timeout=3m' > (Join-Path $PSScriptRoot "windows-$Label.txt") 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Cold-header characterization failed' }
    Get-Content (Join-Path $PSScriptRoot "windows-$Label.txt") -Tail 12
} finally { Pop-Location }
