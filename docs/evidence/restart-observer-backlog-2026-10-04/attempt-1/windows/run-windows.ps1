param([Parameter(Mandatory=$true)][ValidatePattern('^attempt-[1-9][0-9]*$')][string]$Attempt)
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
Set-Location -LiteralPath $workspace
$results = Join-Path $PSScriptRoot ($Attempt + '/windows')
if (Test-Path -LiteralPath $results) { throw 'Evidence already exists' }
New-Item -ItemType Directory -Path $results | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $results 'run-windows.ps1')
$env:GOTOOLCHAIN = 'local'
$env:GOPROXY = 'off'
$env:CGO_ENABLED = '0'
$env:GOMAXPROCS = '2'
$env:GOCACHE = Join-Path $workspace 'tmp/restart-runtime/gocache'
$env:GOPATH = Join-Path $workspace 'tmp/restart-runtime/gopath'
$env:GOTMPDIR = Join-Path $workspace 'tmp/restart-runtime/gotmp'
$env:FUSION_OBSERVE_EVIDENCE = ''
$env:FUSION_HISTORY_EVIDENCE = ''
$env:FUSION_BACKFILL_EVIDENCE = ''
$env:FUSION_TICKET_EVIDENCE = ''
$env:FUSION_HISTORY_COST_EVIDENCE = ''
$env:FUSION_HISTORY_BACKLOG_EVIDENCE = ''
$utf8 = [System.Text.UTF8Encoding]::new($false)
$sources = [ordered]@{}
Get-ChildItem -Path 'cmd/fsn-observe/*.go','internal/observe/*.go','go.mod','go.sum' | Sort-Object FullName | ForEach-Object {
    $relative = [System.IO.Path]::GetRelativePath($workspace, $_.FullName).Replace('\','/')
    $sources[$relative] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
[System.IO.File]::WriteAllText((Join-Path $results 'sources.json'), ($sources | ConvertTo-Json), $utf8)
$baseline = & git rev-parse HEAD
[System.IO.File]::WriteAllText((Join-Path $results 'baseline.txt'), [string]$baseline, $utf8)
$go = Join-Path $workspace 'tmp/restart-runtime/go/bin/go.exe'
$output = & $go version 2>&1
[System.IO.File]::WriteAllLines((Join-Path $results 'toolchain.txt'), [string[]]@($output), $utf8)
$output = & $go test -count=1 -mod=readonly -v -timeout=3m ./internal/observe ./cmd/fsn-observe 2>&1
$result = $LASTEXITCODE
[System.IO.File]::WriteAllLines((Join-Path $results 'tests.txt'), [string[]]@($output), $utf8)
[System.IO.File]::WriteAllText((Join-Path $results 'test-exit.txt'), [string]$result, $utf8)
if ($result -ne 0) { throw "Windows tests failed: $result" }
Write-Output 'Windows observer and command suites passed.'

$env:FUSION_HISTORY_BACKLOG_EVIDENCE = Join-Path $results 'backlog.json'
$output = & $go test -count=1 -mod=readonly -run '^TestHistoryBoundedBacklogAndClosedCopy$' -v -timeout=8m ./internal/observe 2>&1
$result = $LASTEXITCODE
[System.IO.File]::WriteAllLines((Join-Path $results 'backlog-test.txt'), [string[]]@($output), $utf8)
[System.IO.File]::WriteAllText((Join-Path $results 'backlog-exit.txt'), [string]$result, $utf8)
if ($result -ne 0) { throw "Windows backlog test failed: $result" }
Write-Output 'Windows bounded backlog and closed-copy test passed.'
