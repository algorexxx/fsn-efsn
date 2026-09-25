$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$env:CGO_ENABLED = '0'
$env:GOMAXPROCS = '2'
$env:GOTOOLCHAIN = 'local'
$env:GOPROXY = 'off'
$env:GOCACHE = Join-Path $workspace 'tmp/restart-runtime/gocache'
$env:GOPATH = Join-Path $workspace 'tmp/restart-runtime/gopath'
$env:GOTMPDIR = Join-Path $workspace 'tmp/restart-runtime/gotmp'
Push-Location $workspace
try {
    & ./tmp/restart-runtime/go/bin/go.exe test -p=2 -mod=readonly -c -o tmp/snapshot-restore-windows-tests.exe ./tests/restart
    if ($LASTEXITCODE -ne 0) { throw 'Snapshot test build failed' }
} finally {
    Pop-Location
}
