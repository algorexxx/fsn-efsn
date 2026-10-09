$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$archiveRoot = 'W:\FusionRestart\old-tests-archive-v2-2026-10-09'
$encoding = [Text.UTF8Encoding]::new($false)
$copyPath = Join-Path $PSScriptRoot 'copy.json'
$retirePath = Join-Path $PSScriptRoot 'retire.json'
$resultPath = Join-Path $PSScriptRoot 'verification.json'
if (Test-Path -LiteralPath $resultPath) { throw 'Preserve existing verification.' }
$copy = Get-Content -LiteralPath $copyPath -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
$retire = Get-Content -LiteralPath $retirePath -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
$actualBytes = 0L
foreach ($entry in $copy.Entries) {
    foreach ($item in $entry.Inventory.Values) {
        if (-not $item.Directory) { $actualBytes += [long]$item.Bytes }
    }
}
if (-not $copy.Completed -or -not $retire.Completed -or $actualBytes -ne 12382043962 -or $retire.Bytes -ne $actualBytes -or $copy.Bytes -ne $actualBytes) { throw 'Incomplete or unexpected operation.' }
if ($copy.ScriptSHA256 -ne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'recover-copy.ps1')).Hash.ToLowerInvariant() -or $retire.ScriptSHA256 -ne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'retire.ps1')).Hash.ToLowerInvariant() -or $retire.CopyScriptSHA256 -ne $copy.ScriptSHA256) { throw 'Changed operation script.' }
if (($copy.Entries.Name -join '|') -ne ($retire.Entries.Name -join '|') -or $copy.Entries.Count -ne 10) { throw 'Unexpected archive selection.' }
if ((Get-PSDrive W).DisplayRoot -ne '\\192.168.1.250\mnemosyne1') { throw 'Wrong W: mapping.' }
foreach ($name in @('copy.json', 'retire.json')) {
    if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $name)).Hash -ne (Get-FileHash -LiteralPath (Join-Path $archiveRoot $name)).Hash) { throw 'Archive manifest differs.' }
}
$counts = @()
foreach ($entry in $copy.Entries) {
    if ($entry.Source -ne (Join-Path 'D:\FusionRehearsal' $entry.Name) -or $entry.Archive -ne (Join-Path $archiveRoot $entry.Name)) { throw 'Unexpected paths.' }
    if (Test-Path -LiteralPath $entry.Source) { throw 'Retired local root still exists.' }
    $entries = @(Get-ChildItem -LiteralPath $entry.Archive -Recurse -Force | Sort-Object FullName)
    $relative = @($entries | ForEach-Object { $_.FullName.Substring($entry.Archive.Length+1).Replace('\', '/') })
    if (($relative -join '|') -cne ($entry.Inventory.Keys -join '|')) { throw 'Archive contents differ after removal.' }
    foreach ($item in $entries) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected archive link.' }
        $expected = $entry.Inventory[$item.FullName.Substring($entry.Archive.Length+1).Replace('\', '/')]
        if ($item.PSIsContainer -ne $expected.Directory -or (-not $item.PSIsContainer -and $item.Length -ne $expected.Bytes)) { throw 'Archive size/type mismatch.' }
    }
    $counts += [ordered]@{ Name=$entry.Name; Files=@($entries | Where-Object { -not $_.PSIsContainer }).Count; SourceAbsent=$true; ArchiveInventoryMatches=$true }
}
$before = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'protected-before.json') -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
$vhd = Get-Item -LiteralPath 'D:\FusionRehearsal\Ubuntu\ext4.vhdx'
$protectedStatePath = Join-Path $PSScriptRoot 'protected-state.json'
$protectedState = Get-Content -LiteralPath $protectedStatePath -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
if (-not $protectedState.pass_ -or -not $protectedState.working.all_sha256_match -or -not $protectedState.recovery.all_sha256_match -or $protectedState.working.files -ne 3514 -or $protectedState.recovery.files -ne 1383) { throw 'Protected database inventories failed.' }
if ($protectedState.script_sha256 -ne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'protected-state-check.py')).Hash.ToLowerInvariant()) { throw 'Changed protected-state inspection script.' }
$vhdMetadataUnchanged = $vhd.Length -eq $before.Vhd.Length -and $vhd.LastWriteTimeUtc.Ticks -eq $before.Vhd.ModifiedUtcTicks
$remaining = @(Get-ChildItem -LiteralPath 'D:\FusionRehearsal' -Force | Select-Object -ExpandProperty Name | Sort-Object)
$expectedRemaining = @($before.SourceRootNames | Where-Object { $_ -notin $copy.Entries.Name } | Sort-Object)
if (($remaining -join '|') -cne ($expectedRemaining -join '|')) { throw 'Unexpected remaining D: roots.' }
$free = (Get-PSDrive D).Free
if ($free -le 60GB -or $free - $copy.DFreeBefore -lt 10GB) { throw 'Expected host D: space not recovered.' }
$result = [ordered]@{ Pass=$true; Finished=[DateTime]::UtcNow.ToString('o'); Files=($counts.Files | Measure-Object -Sum).Sum; LogicalBytes=$actualBytes; OriginalCopySummaryFailed=$true; CompleteCopyInventoryReconstructedAndReverified=$true; DFreeBefore=$copy.DFreeBefore; DFreeAfter=$free; DFreeIncrease=$free-$copy.DFreeBefore; ArchiveBytesReverifiedBeforeRemoval=$true; FinalArchiveNamesAndSizesMatch=$true; ProtectedVhdMetadataUnchanged=$vhdMetadataUnchanged; ProtectedFilesVerified=$true; ProtectedStateSHA256=(Get-FileHash -LiteralPath $protectedStatePath).Hash.ToLowerInvariant(); OtherDRootNamesUnchanged=$true; CopySHA256=(Get-FileHash -LiteralPath $copyPath).Hash.ToLowerInvariant(); RetireSHA256=(Get-FileHash -LiteralPath $retirePath).Hash.ToLowerInvariant(); Entries=$counts }
[IO.File]::WriteAllText($resultPath, ($result | ConvertTo-Json -Depth 6) + "`n", $encoding)
$result | ConvertTo-Json -Depth 6
