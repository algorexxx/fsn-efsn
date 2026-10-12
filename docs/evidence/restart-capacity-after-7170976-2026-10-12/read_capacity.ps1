$ErrorActionPreference = 'Stop'
$capacityOutput = Join-Path $PSScriptRoot 'host-capacity.json'
if (Test-Path -LiteralPath $capacityOutput) { throw 'Preserve the existing capacity record' }
$capacityRecord = [ordered]@{
    observed = [DateTime]::UtcNow.ToString('o')
    volumes = @(Get-Volume -DriveLetter C,D | Select-Object DriveLetter,Size,SizeRemaining)
    rehearsalRoot = 'D:\FusionRehearsal'
    rehearsalEntries = @(Get-ChildItem -LiteralPath 'D:\FusionRehearsal' -Force | Select-Object Name,Mode,Length)
    rehearsalVhd = Get-Item -LiteralPath 'D:\FusionRehearsal\Ubuntu\ext4.vhdx' | Select-Object FullName,Length,LastWriteTimeUtc,Attributes
    archive = @(Get-PSDrive -Name W | Select-Object Name,Root,DisplayRoot,Free,Used)
    scope = 'Host free space and metadata only; no file content hashes, moves, deletions, expansion or compaction'
}
$capacityJson = $capacityRecord | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($capacityOutput, $capacityJson + "`n", [System.Text.UTF8Encoding]::new($false))
$capacityJson
