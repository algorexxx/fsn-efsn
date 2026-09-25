$ErrorActionPreference = 'Stop'
$addressWorkspace = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
& (Join-Path $addressWorkspace 'tmp/peer-addresses-windows-tests.exe') '-test.run=^TestRestartPeer(Address|Replacement|Stale|Repeated)' '-test.v' '-test.timeout=30s' 2>&1 | Out-File -LiteralPath (Join-Path $PSScriptRoot 'windows-tests.txt') -Encoding utf8 -Width 4096
$addressTestExit = $LASTEXITCODE
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-tests.txt') -Tail 18
exit $addressTestExit
