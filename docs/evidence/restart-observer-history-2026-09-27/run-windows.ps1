$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location -LiteralPath $workspace
$env:GOTOOLCHAIN = 'local'
$env:GOPROXY = 'off'
$env:CGO_ENABLED = '0'
$env:GOCACHE = Join-Path $workspace 'tmp/restart-runtime/gocache'
$env:GOPATH = Join-Path $workspace 'tmp/restart-runtime/gopath'
$env:GOTMPDIR = Join-Path $workspace 'tmp/restart-runtime/gotmp'
$env:FUSION_OBSERVE_EVIDENCE = ''
$env:FUSION_HISTORY_EVIDENCE = Join-Path $PSScriptRoot 'windows-history'
$utf8 = [System.Text.UTF8Encoding]::new($false)
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'windows.txt')) { throw 'Evidence already exists' }
New-Item -ItemType Directory -Path $env:FUSION_HISTORY_EVIDENCE -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path 'tmp/restart-observer-history' -Force | Out-Null
$go = Join-Path $workspace 'tmp/restart-runtime/go/bin/go.exe'
$output = & $go version 2>&1
[System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot 'windows-toolchain.txt'), [string[]]@($output), $utf8)
$output = & $go test -count=1 -mod=readonly -v -timeout=2m ./internal/observe ./cmd/fsn-observe 2>&1
$result = $LASTEXITCODE
[System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot 'windows.txt'), [string[]]@($output), $utf8)
if ($result -ne 0) { throw "Windows tests failed: $result" }
$output = & $go build -mod=readonly -o tmp/restart-observer-history/fsn-observe.exe ./cmd/fsn-observe 2>&1
$result = $LASTEXITCODE
[System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot 'windows-build.txt'), [string[]]@($output), $utf8)
if ($result -ne 0) { throw "Windows build failed: $result" }
Remove-Item Env:FUSION_HISTORY_EVIDENCE
Write-Output 'Windows history/collector tests and build passed.'
