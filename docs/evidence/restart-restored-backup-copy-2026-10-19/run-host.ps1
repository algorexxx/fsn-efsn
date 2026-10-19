$ErrorActionPreference = 'Stop'
$copyRoot = $PSScriptRoot
if (Test-Path -LiteralPath (Join-Path $copyRoot 'host-run.json')) { throw 'Existing job must be preserved' }
$copyMapping = Get-SmbMapping -LocalPath 'W:'
if ($copyMapping.RemotePath -ne '\\192.168.1.250\mnemosyne1' -or $copyMapping.Status -ne 'OK') { throw 'Unexpected W: mapping' }
$copyStart = [DateTimeOffset]::UtcNow.ToString('o')
$copyMapping | Select-Object LocalPath,RemotePath,Status | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $copyRoot 'mapping.json') -Encoding utf8
$copyArgs = @('-d','FusionRehearsal','-u','root','--','timeout','--kill-after=20s','28800s','python3','-B','/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-restored-backup-copy-2026-10-19/launch.py')
& wsl.exe @copyArgs 1> (Join-Path $copyRoot 'host.stdout.txt') 2> (Join-Path $copyRoot 'host.stderr.txt')
$copyExit = $LASTEXITCODE
@{started=$copyStart;finished=[DateTimeOffset]::UtcNow.ToString('o');exit=$copyExit;argv=$copyArgs} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $copyRoot 'host-run.json') -Encoding utf8
exit $copyExit
