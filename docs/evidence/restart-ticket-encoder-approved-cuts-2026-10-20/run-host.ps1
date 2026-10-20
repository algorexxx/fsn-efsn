$ErrorActionPreference = 'Stop'
$operatorRoot = $PSScriptRoot
if (Test-Path -LiteralPath (Join-Path $operatorRoot 'host-run.json')) { throw 'Preserve existing attempt' }
$operatorMemory = [long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory * 1024
if ($operatorMemory -lt 2GB) { throw 'At least 2 GiB available host RAM required' }
if ((Get-PSDrive C).Free -lt 50GB -or (Get-PSDrive D).Free -lt 50GB) { throw 'Insufficient host reserve' }
$operatorImages = @(
    'W:\FusionRestart\replay-work-7170976-2026-10-12\replay.ext4',
    'W:\FusionRestart\restored-backup-2026-10-19\startup.ext4'
)
$operatorBefore = @{}
foreach ($operatorImage in $operatorImages) {
    $operatorItem = Get-Item -LiteralPath $operatorImage
    $operatorBefore[$operatorImage] = @{length=$operatorItem.Length;modified=$operatorItem.LastWriteTimeUtc.ToString('o')}
}
@{checked=[DateTimeOffset]::UtcNow.ToString('o');free_bytes=@{C=(Get-PSDrive C).Free;D=(Get-PSDrive D).Free};available_memory_bytes=$operatorMemory;protected_images=$operatorBefore} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $operatorRoot 'host-preflight.json') -Encoding utf8
$operatorStarted = [DateTimeOffset]::UtcNow.ToString('o')
$operatorArgs = @('-d','FusionRehearsal','-u','root','--','timeout','--kill-after=20s','2400s','python3','-B','/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-ticket-encoder-approved-cuts-2026-10-20/launch.py')
& wsl.exe @operatorArgs 1> (Join-Path $operatorRoot 'host.stdout.txt') 2> (Join-Path $operatorRoot 'host.stderr.txt')
$operatorCode = $LASTEXITCODE
$operatorUnchanged = $true
foreach ($operatorImage in $operatorImages) {
    $operatorItem = Get-Item -LiteralPath $operatorImage
    if ($operatorItem.Length -ne $operatorBefore[$operatorImage].length -or $operatorItem.LastWriteTimeUtc.ToString('o') -ne $operatorBefore[$operatorImage].modified) { $operatorUnchanged = $false }
}
@{started=$operatorStarted;finished=[DateTimeOffset]::UtcNow.ToString('o');exit=$operatorCode;argv=$operatorArgs;protected_images_unchanged=$operatorUnchanged;free_bytes=@{C=(Get-PSDrive C).Free;D=(Get-PSDrive D).Free}} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $operatorRoot 'host-run.json') -Encoding utf8
if (-not $operatorUnchanged) { throw 'Protected image metadata changed' }
exit $operatorCode
