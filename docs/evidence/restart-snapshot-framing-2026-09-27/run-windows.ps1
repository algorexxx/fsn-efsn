$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location -LiteralPath $workspace
$env:GOTOOLCHAIN = 'local'
$env:GOPROXY = 'off'
$env:CGO_ENABLED = '0'
$env:GOCACHE = Join-Path $workspace 'tmp/restart-runtime/gocache'
$env:GOPATH = Join-Path $workspace 'tmp/restart-runtime/gopath'
$env:GOTMPDIR = Join-Path $workspace 'tmp/restart-runtime/gotmp'
$utf8 = [System.Text.UTF8Encoding]::new($false)
$outputDirectory = Join-Path $PSScriptRoot 'after-windows'
New-Item -ItemType Directory -Path $outputDirectory -ErrorAction Stop | Out-Null
$go = Join-Path $workspace 'tmp/restart-runtime/go/bin/go.exe'
$output = & $go version 2>&1
[System.IO.File]::WriteAllLines((Join-Path $outputDirectory 'toolchain.txt'), [string[]]@($output), $utf8)
$inputs = [ordered]@{}
$paths = @('consensus/datong/snapshot.go', 'consensus/datong/snapshot_test.go', 'go.mod', 'go.sum', 'docs/evidence/restart-2026-09-23/responses.json')
$paths += Get-ChildItem -LiteralPath 'tests/restart' -Filter '*_test.go' | ForEach-Object { 'tests/restart/' + $_.Name }
foreach ($path in $paths) { $inputs[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
[System.IO.File]::WriteAllText((Join-Path $outputDirectory 'inputs.sha256.json'), ($inputs | ConvertTo-Json) + "`n", $utf8)
$output = & $go test -count=1 -mod=readonly -v -timeout=1m ./consensus/datong 2>&1
$result = $LASTEXITCODE
[System.IO.File]::WriteAllLines((Join-Path $outputDirectory 'parser.txt'), [string[]]@($output), $utf8)
if ($result -ne 0) { throw "Parser tests failed: $result" }
$output = & $go test -count=1 -mod=readonly -v -timeout=3m -run '^(TestHeaderBatchUsesUnstoredParents|TestFinalizeParentIsolatedFromConcurrentImport|TestColdHeaderValidationBoundaries)$' ./tests/restart 2>&1
$result = $LASTEXITCODE
[System.IO.File]::WriteAllLines((Join-Path $outputDirectory 'compatibility.txt'), [string[]]@($output), $utf8)
[System.IO.File]::WriteAllText((Join-Path $outputDirectory 'exit.txt'), "$result`n", $utf8)
if ($result -ne 0) { throw "Compatibility tests failed: $result" }
Write-Output 'Windows parser and existing header/import compatibility tests passed.'
