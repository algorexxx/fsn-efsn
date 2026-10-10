$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$sourceRoot = 'D:\FusionRehearsal'
$archiveRoot = 'W:\FusionRestart\old-fixtures-copy-2026-10-10'
$repository = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$names = @('abandonment-reorg-2026-09-27', 'equal-weight-2026-09-27', 'stale-intent-2026-09-27', 'live-abandonment-repair-2026-09-27')
$encoding = [Text.UTF8Encoding]::new($false)
$locks = [Collections.Generic.List[IO.FileStream]]::new()
$deadline = [DateTime]::UtcNow.AddHours(2)

function Save-Record($name, $value) {
    $path = Join-Path $PSScriptRoot $name
    if (Test-Path -LiteralPath $path) { throw "Preserve existing record: $name" }
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 12) + "`n", $encoding)
}

function Assert-Idle {
    if ([DateTime]::UtcNow -gt $deadline) { throw 'Two-hour operation limit exceeded.' }
    $running = ((& wsl.exe --list --running --quiet) -join "`n").Replace([string][char]0, '')
    if ($LASTEXITCODE -ne 0 -or $running.Contains('FusionRehearsal')) { throw 'FusionRehearsal must be stopped.' }
    $active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(efsn|replay-tests|restart-tests|observer)$' })
    if ($active.Count) { throw 'A native rehearsal executable is running.' }
    if ((Get-PSDrive W).DisplayRoot -ne '\\192.168.1.250\mnemosyne1') { throw 'Unexpected W: mapping.' }
    if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive W).Free -lt 100GB) { throw 'Storage reserve failed.' }
}

function Assert-Path($path, $root) {
    $full = [IO.Path]::GetFullPath($path)
    if ($full -ne $path -or -not $full.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Out-of-scope path: $path" }
    $current = Get-Item -LiteralPath $path -Force
    while ($null -ne $current -and $current.FullName.Length -ge $root.Length) {
        if ($current.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $path" }
        $current = if ($current -is [IO.DirectoryInfo]) { $current.Parent } else { $current.Directory }
    }
}

function Get-Inventory($path) {
    $result = [ordered]@{}
    foreach ($item in @(Get-ChildItem -LiteralPath $path -Recurse -Force | Sort-Object FullName)) {
        Assert-Path $item.FullName $path
        $relative = $item.FullName.Substring($path.Length + 1).Replace('\', '/')
        $result[$relative] = [ordered]@{ Directory=$item.PSIsContainer; Bytes=$(if ($item.PSIsContainer) { 0L } else { $item.Length }); ModifiedUtcTicks=$item.LastWriteTimeUtc.Ticks; Attributes=[int]$item.Attributes }
    }
    return $result
}

function Get-Digest($path) {
    return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-Inventory($path, $expected, [bool]$source) {
    $actual = Get-Inventory $path
    if (($actual.Keys -join "`n") -cne ($expected.Keys -join "`n")) { throw "Changed inventory: $path" }
    foreach ($relative in $expected.Keys) {
        $a = $actual[$relative]
        $e = $expected[$relative]
        if ($a.Directory -ne $e.Directory -or $a.Bytes -ne $e.Bytes) { throw "Changed size/type: $relative" }
        if ($source -and ($a.ModifiedUtcTicks -ne $e.ModifiedUtcTicks -or $a.Attributes -ne $e.Attributes)) { throw "Changed metadata: $relative" }
        if (-not $e.Directory -and (Get-Digest (Join-Path $path $relative)) -cne $e.SHA256) { throw "Changed bytes: $relative" }
    }
}

function Assert-Evidence($name) {
    $bundle = Join-Path $repository ('docs\evidence\restart-' + $name)
    $manifest = Join-Path $bundle 'SHA256SUMS'
    foreach ($line in [IO.File]::ReadAllLines($manifest, $encoding)) {
        if ($line -notmatch '^([0-9a-f]{64})\s+(.+)$') { throw "Malformed evidence manifest: $name" }
        $digest = $Matches[1]
        $file = [IO.Path]::GetFullPath((Join-Path $bundle $Matches[2]))
        Assert-Path $file $bundle
        if ((Get-Digest $file) -cne $digest) { throw "Changed sealed evidence: $name" }
    }
    return [ordered]@{ Bundle=$bundle; ManifestSHA256=(Get-Digest $manifest) }
}



$copyBundle = Join-Path $repository 'docs\evidence\restart-old-fixtures-copy-w-2026-10-10'
$record = [ordered]@{ Mode='Retire'; Started=[DateTime]::UtcNow.ToString('o'); ScriptSHA256=(Get-Digest $PSCommandPath); DFreeBefore=(Get-PSDrive D).Free; WFreeBefore=(Get-PSDrive W).Free; Entries=@(); Completed=$false }
try {
    Assert-Idle
    foreach ($manifest in @((Join-Path $PSScriptRoot 'INPUT_SHA256SUMS'), (Join-Path $copyBundle 'SHA256SUMS'))) {
        foreach ($line in [IO.File]::ReadAllLines($manifest, $encoding)) {
            if ($line -notmatch '^([0-9a-f]{64})\s+(.+)$') { throw 'Malformed manifest.' }
            $file = [IO.Path]::GetFullPath((Join-Path (Split-Path $manifest) $Matches[2]))
            $expected = $Matches[1]
            Assert-Path $file (Split-Path $manifest)
            if ((Get-Digest $file) -cne $expected) { throw 'Changed sealed input.' }
        }
    }
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'retire.json')) { throw 'Operation already recorded.' }
    Assert-Path $archiveRoot 'W:\FusionRestart'
    $previous = Get-Content -LiteralPath (Join-Path $copyBundle 'copy.json') -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
    $completion = Get-Content -LiteralPath (Join-Path $copyBundle 'completion.json') -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
    if ($completion.exit -ne 0 -or -not $previous.Completed -or $previous.Mode -cne 'CopyOnly' -or $previous.ScriptSHA256 -cne (Get-Digest (Join-Path $copyBundle 'copy.ps1')) -or ($previous.Entries.Name -join '|') -cne ($names -join '|')) { throw 'Invalid copy record.' }
    if ($previous.Bytes -ne 4737656365L -or $previous.Files -ne 3705L -or $previous.RemovedSources.Count -ne 0) { throw 'Unexpected copy totals.' }
    if ((Get-Digest (Join-Path $copyBundle 'copy.json')) -cne (Get-Digest (Join-Path $archiveRoot 'copy.json'))) { throw 'Archive record mismatch.' }
    $record.OtherRootsBefore = @(Get-ChildItem -LiteralPath $sourceRoot -Force | Where-Object { $_.Name -notin $names } | Sort-Object Name | ForEach-Object { $_.Name })
    foreach ($name in $names) {
        $source = Join-Path $sourceRoot $name
        Assert-Path $source $sourceRoot
        foreach ($file in @(Get-ChildItem -LiteralPath $source -Recurse -File -Force | Where-Object { $_.Name -eq 'LOCK' -or $_.Name -like '*.run.lock' })) {
            Assert-Path $file.FullName $source
            $locks.Add([IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read))
        }
    }
    if ($locks.Count -eq 0) { throw 'No database lock handles found.' }
    $record.LockHandles = $locks.Count
    foreach ($entry in $previous.Entries) {
        Assert-Idle
        if ($entry.Source -cne (Join-Path $sourceRoot $entry.Name) -or $entry.Archive -cne (Join-Path $archiveRoot $entry.Name) -or $entry.Name -notin $names) { throw 'Record outside exact allowlist.' }
        Assert-Path $entry.Source $sourceRoot
        Assert-Path $entry.Archive $archiveRoot
        $evidence = Assert-Evidence $entry.Name
        if ($evidence.ManifestSHA256 -cne $entry.Evidence.ManifestSHA256) { throw 'Changed evidence manifest.' }
        Assert-Inventory $entry.Source $entry.Inventory $true
        Assert-Inventory $entry.Archive $entry.Inventory $false
        $record.Entries += $entry
        Write-Output ('Verified source and archive: ' + $entry.Name)
    }
        Save-Record 'retire-ready.json' ([ordered]@{ Time=[DateTime]::UtcNow.ToString('o'); CopySHA256=(Get-Digest (Join-Path $copyBundle 'copy.json')); Sources=@($record.Entries.Source) })
        foreach ($entry in $record.Entries) {
            Assert-Idle
            Assert-Path $entry.Source $sourceRoot
            if ($entry.Source -cne (Join-Path $sourceRoot $entry.Name) -or $entry.Name -notin $names) { throw 'Deletion target is outside the exact allowlist.' }
            foreach ($handle in $locks) { if ($handle.Name.StartsWith($entry.Source + '\', [StringComparison]::OrdinalIgnoreCase)) { $handle.Dispose() } }
            foreach ($relative in $entry.Inventory.Keys) {
                if ($entry.Inventory[$relative].Directory) { continue }
                $file = Join-Path $entry.Source $relative
                Assert-Path $file $entry.Source
                $info = Get-Item -LiteralPath $file -Force
                if ($info.Length -ne $entry.Inventory[$relative].Bytes -or $info.LastWriteTimeUtc.Ticks -ne $entry.Inventory[$relative].ModifiedUtcTicks) { throw 'Source changed before removal.' }
                if ([DateTime]::UtcNow -gt $deadline) { throw 'Two-hour operation limit exceeded.' }
                Remove-Item -LiteralPath $file -Force
            }
            foreach ($relative in @($entry.Inventory.Keys | Where-Object { $entry.Inventory[$_].Directory } | Sort-Object Length -Descending)) {
                $directory = Join-Path $entry.Source $relative
                Assert-Path $directory $entry.Source
                [IO.Directory]::Delete($directory, $false)
            }
            [IO.Directory]::Delete($entry.Source, $false)
            if (Test-Path -LiteralPath $entry.Source) { throw 'Source remains after removal.' }
            Save-Record ($entry.Name+'-retired.json') ([ordered]@{ Source=$entry.Source; Archive=$entry.Archive; Removed=[DateTime]::UtcNow.ToString('o') })
            Write-Output ('Retired ' + $entry.Name)
        }

    $record.OtherRootsAfter = @(Get-ChildItem -LiteralPath $sourceRoot -Force | Sort-Object Name | ForEach-Object { $_.Name })
    if (($record.OtherRootsBefore -join '|') -cne ($record.OtherRootsAfter -join '|')) { throw 'Unexpected change to retained roots.' }
    $record.SourceRootsAbsent = @($names | ForEach-Object { -not (Test-Path -LiteralPath (Join-Path $sourceRoot $_)) })
    if ($record.SourceRootsAbsent -contains $false) { throw 'Retired root remains.' }
    $record.Bytes = $previous.Bytes
    $record.Files = $previous.Files
    $record.CopySHA256 = Get-Digest (Join-Path $copyBundle 'copy.json')
    $record.Completed = $true
    $record.Finished = [DateTime]::UtcNow.ToString('o')
    $record.DFreeAfter = (Get-PSDrive D).Free
    $record.WFreeAfter = (Get-PSDrive W).Free
    Save-Record 'retire.json' $record
    $archiveRecord = Join-Path $archiveRoot 'retire.json'
    if (Test-Path -LiteralPath $archiveRecord) { throw 'Archive retirement record already exists.' }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'retire.json') -Destination $archiveRecord
    if ((Get-Digest (Join-Path $PSScriptRoot 'retire.json')) -cne (Get-Digest $archiveRecord)) { throw 'Final record mismatch.' }
    Write-Output (([ordered]@{ Completed='Retire'; Bytes=$record.Bytes; Files=$record.Files; DFree=$record.DFreeAfter }) | ConvertTo-Json -Compress)
} catch {
    Save-Record 'retire-failure.json' ([ordered]@{ Time=[DateTime]::UtcNow.ToString('o'); Error=$_.ToString(); Stack=$_.ScriptStackTrace })
    throw
} finally {
    foreach ($handle in $locks) { $handle.Dispose() }
}
