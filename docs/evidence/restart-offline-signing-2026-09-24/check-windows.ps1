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
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
Push-Location $workspace
try {
    & ./tmp/restart-runtime/go/bin/go.exe test -p=2 -mod=readonly -count=1 -v ./internal/recovery ./cmd/fsn-recovery 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'windows-unit-final.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Offline unit tests failed' }
    & ./tmp/restart-runtime/go/bin/go.exe test -p=2 -mod=readonly -c -o tmp/recovery-offline-windows-tests.exe ./tests/restart
    if ($LASTEXITCODE -ne 0) { throw 'Offline restart tests did not compile' }
    Set-Location tests/restart
    & ../../tmp/recovery-offline-windows-tests.exe '-test.run=^Test(OfflineRecovery(ProcessCuts|UncertainCuts|Refusals)|Recovery(Guard|GuardRejects|GuardInsufficientReplacement|JournalHandover))$' '-test.v' '-test.timeout=3m' 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'windows-integration-final.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Offline process rehearsal failed' }
} finally {
    Pop-Location
}
