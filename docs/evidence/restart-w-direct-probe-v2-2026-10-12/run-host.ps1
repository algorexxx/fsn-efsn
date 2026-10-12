$ErrorActionPreference = 'Stop'
$probeRoot = $PSScriptRoot
if (Test-Path -LiteralPath (Join-Path $probeRoot 'host-run.json')) { throw 'Existing run must be preserved' }
$probeMapping = Get-SmbMapping -LocalPath 'W:'
if ($probeMapping.RemotePath -ne '\\192.168.1.250\mnemosyne1' -or $probeMapping.Status -ne 'OK') { throw 'Unexpected W: mapping' }
$probeStart = [DateTimeOffset]::UtcNow.ToString('o')
$probeMapping | Select-Object LocalPath,RemotePath,Status | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $probeRoot 'mapping.json') -Encoding utf8
$probeArgs = @('-d','FusionRehearsal','-u','root','--','timeout','--kill-after=10s','330s','python3','-B','/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-w-direct-probe-v2-2026-10-12/run.py')
& wsl.exe @probeArgs 1> (Join-Path $probeRoot 'host.stdout.txt') 2> (Join-Path $probeRoot 'host.stderr.txt')
$probeExit = $LASTEXITCODE
@{started=$probeStart;finished=[DateTimeOffset]::UtcNow.ToString('o');exit=$probeExit;argv=$probeArgs} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $probeRoot 'host-run.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $probeRoot 'host-run.json') -Encoding utf8
exit $probeExit
