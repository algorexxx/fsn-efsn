$ErrorActionPreference = 'Stop'
$bootstrapWorkspace = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
& (Join-Path $bootstrapWorkspace 'tmp/bootstrap-dns-windows-tests.exe') '-test.run=^TestRestartBootstrap' '-test.v' '-test.timeout=30s' 2>&1 | Out-File -LiteralPath (Join-Path $PSScriptRoot 'windows-tests.txt') -Encoding utf8 -Width 4096
$bootstrapTestExit = $LASTEXITCODE
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-tests.txt') -Tail 18
exit $bootstrapTestExit
