$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$binary = Join-Path $workspace 'tmp/state-export-verify-windows.exe'
$writer = Join-Path $workspace 'tmp/state-export-writer-linux'
$artifact = Join-Path $workspace 'tmp/preserved-head-state'
if ((Get-FileHash $writer -Algorithm SHA256).Hash.ToLowerInvariant() -ne '2d1bc97226a0323428bde9fe3617d5628e28985a6208457266547098c31a8231') {
    throw 'Retained writer hash differs'
}
$env:GOMAXPROCS = '2'
$env:FUSION_RESTART_CHAINDATA = ''
$env:FUSION_RESTART_VERIFY_EXPORT_DIR = ''
$env:FUSION_RESTART_STATE_EXPORT_WRITER = ''
Push-Location (Join-Path $workspace 'tests/restart')
try {
    & $binary '-test.run=^TestStateExport' '-test.v' '-test.count=1' '-test.timeout=3m' > (Join-Path $PSScriptRoot 'portable-focused-windows.txt') 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Portable extraction tests failed' }
    $env:FUSION_RESTART_VERIFY_EXPORT_DIR = $artifact
    & $binary '-test.run=^TestVerifyStateExport$' '-test.v' '-test.timeout=30s' > (Join-Path $PSScriptRoot 'windows-verify-wrong-writer.txt') 2>&1
    if ($LASTEXITCODE -eq 0 -or -not (Select-String -Path (Join-Path $PSScriptRoot 'windows-verify-wrong-writer.txt') -Pattern 'export identity does not match' -Quiet)) {
        throw 'Wrong writer was not rejected as expected'
    }
    if (Test-Path (Join-Path $artifact 'verified.json')) { throw 'Unexpected verification marker before valid native verification' }
    $env:FUSION_RESTART_STATE_EXPORT_WRITER = $writer
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'windows-verify-started.txt'), [DateTime]::UtcNow.ToString('o') + "`n", [Text.UTF8Encoding]::new($false))
    & $binary '-test.run=^TestVerifyStateExport$' '-test.v' '-test.timeout=45m' > (Join-Path $PSScriptRoot 'windows-verify.txt') 2>&1
    $code = $LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'windows-verify-exit-code.txt'), "$code`n", [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'windows-verify-finished.txt'), [DateTime]::UtcNow.ToString('o') + "`n", [Text.UTF8Encoding]::new($false))
    Get-Content (Join-Path $PSScriptRoot 'windows-verify.txt') -Tail 8
    if ($code -ne 0) { throw 'Native state verification failed' }
} finally {
    Pop-Location
}
