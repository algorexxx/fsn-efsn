$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$sourceRoot = 'D:\FusionRehearsal'
$archiveRoot = 'W:\FusionRestart\remaining-fixtures-copy-2026-10-10'
$repository = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$proposal = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'proposal.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$names = @($proposal.Entries.Name)
if ($names.Count -ne 14 -or @($names | Select-Object -Unique).Count -ne 14) { throw 'Unexpected source allowlist.' }
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
    if ((Get-PSDrive C).Free -lt 5GB -or (Get-PSDrive W).Free -lt 100GB) { throw 'Storage reserve failed.' }
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
    $entry = @($proposal.Entries | Where-Object { $_.Name -ceq $name })
    if ($entry.Count -ne 1 -or $entry[0].EvidenceBundle -notmatch '^restart-[a-z0-9-]+$') { throw 'Invalid evidence mapping.' }
    $bundle = Join-Path $repository ('docs\evidence\' + $entry[0].EvidenceBundle)
    $manifest = Join-Path $bundle 'SHA256SUMS'
    if ((Get-Digest $manifest) -cne $entry[0].EvidenceManifestSHA256) { throw 'Evidence manifest differs from the reviewed proposal.' }
    foreach ($line in [IO.File]::ReadAllLines($manifest, $encoding)) {
        if ($line -notmatch '^([0-9a-f]{64})\s+(.+)$') { throw "Malformed evidence manifest: $name" }
        $digest = $Matches[1]
        $file = [IO.Path]::GetFullPath((Join-Path $bundle $Matches[2]))
        Assert-Path $file $bundle
        if ((Get-Digest $file) -cne $digest) { throw "Changed sealed evidence: $name" }
    }
    return [ordered]@{ Bundle=$bundle; ManifestSHA256=(Get-Digest $manifest) }
}


$record = [ordered]@{ Mode='CopyOnly'; Started=[DateTime]::UtcNow.ToString('o'); ScriptSHA256=(Get-Digest $PSCommandPath); DFreeBefore=(Get-PSDrive D).Free; WFreeBefore=(Get-PSDrive W).Free; Entries=@(); Completed=$false; RemovedSources=@() }
try {
    Assert-Idle
    $vhd = Get-Item -LiteralPath 'D:\FusionRehearsal\Ubuntu\ext4.vhdx'
    $record.ProtectedVhdBefore = [ordered]@{ Length=$vhd.Length; ModifiedUtcTicks=$vhd.LastWriteTimeUtc.Ticks }
    $record.OtherRootsBefore = @(Get-ChildItem -LiteralPath $sourceRoot -Force | Sort-Object Name | ForEach-Object { $_.Name })
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'copy.json')) { throw 'Operation already recorded.' }
    foreach ($line in [IO.File]::ReadAllLines((Join-Path $PSScriptRoot 'INPUT_SHA256SUMS'), $encoding)) {
        if ($line -notmatch '^([0-9a-f]{64})\s+(.+)$') { throw 'Malformed input manifest.' }
        if ((Get-Digest (Join-Path $PSScriptRoot $Matches[2])) -cne $Matches[1]) { throw 'Changed archive input.' }
    }
    if (Test-Path -LiteralPath $archiveRoot) { throw 'Archive destination already exists.' }
    [IO.Directory]::CreateDirectory($archiveRoot) | Out-Null
    Assert-Path $archiveRoot 'W:\FusionRestart'
    foreach ($name in $names) {
        $source = Join-Path $sourceRoot $name
        Assert-Path $source $sourceRoot
        foreach ($file in @(Get-ChildItem -LiteralPath $source -Recurse -File -Force | Where-Object { $_.Name -eq 'LOCK' -or $_.Name -like '*.run.lock' })) {
            Assert-Path $file.FullName $source
            $locks.Add([IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read))
        }
    }
    if ($locks.Count -lt 14) { throw 'No database lock handles found.' }
    $record.LockHandles = $locks.Count
    foreach ($name in $names) {
        Assert-Idle
        $source = Join-Path $sourceRoot $name
        $destination = Join-Path $archiveRoot $name
        $evidence = Assert-Evidence $name
        $inventory = Get-Inventory $source
        $review = @($proposal.Entries | Where-Object { $_.Name -ceq $name })[0]
        $observedFiles = @($inventory.Values | Where-Object { -not $_.Directory })
        $observedBytes = 0L
        foreach ($item in $observedFiles) { $observedBytes += [long]$item.Bytes }
        if ($review.Source -cne $source -or $observedFiles.Count -ne $review.Files -or $observedBytes -ne $review.LogicalBytes) { throw 'Source differs from reviewed inventory.' }
        $staging = $destination + '.incomplete'
        if (Test-Path -LiteralPath $staging) { throw 'Staging exists.' }
        [IO.Directory]::CreateDirectory($staging) | Out-Null
        foreach ($relative in $inventory.Keys) {
            if ([DateTime]::UtcNow -gt $deadline) { throw 'Two-hour operation limit exceeded.' }
            $from = Join-Path $source $relative
            $to = Join-Path $staging $relative
            if ($inventory[$relative].Directory) { [IO.Directory]::CreateDirectory($to) | Out-Null; continue }
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to)) | Out-Null
            $inventory[$relative].SHA256 = Get-Digest $from
            Copy-Item -LiteralPath $from -Destination $to
            $flush = [IO.File]::Open($to, [IO.FileMode]::Open, [IO.FileAccess]::Write, [IO.FileShare]::Read)
            try { $flush.Flush($true) } finally { $flush.Dispose() }
            [IO.File]::SetLastWriteTimeUtc($to, [DateTime]::new($inventory[$relative].ModifiedUtcTicks, [DateTimeKind]::Utc))
        }
        Assert-Inventory $source $inventory $true
        Assert-Inventory $staging $inventory $false
        Assert-Idle
        Assert-Path $staging $archiveRoot
        if ([IO.Path]::GetFullPath($destination) -cne $destination -or -not $destination.StartsWith($archiveRoot+'\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Archive rename target is outside the exact root.' }
        if (Test-Path -LiteralPath $destination) { throw 'Final destination exists.' }
        Move-Item -LiteralPath $staging -Destination $destination
        Assert-Path $destination $archiveRoot
        $entry = [ordered]@{ Name=$name; Source=$source; Archive=$destination; Evidence=$evidence; Inventory=$inventory; Verified=[DateTime]::UtcNow.ToString('o') }
        Save-Record ($name+'.manifest.json') $entry
        $record.Entries += $entry
        Write-Output (([ordered]@{ Stage='CopyOnly'; Verified=$name; Files=@($entry.Inventory.Values | Where-Object { -not $_.Directory }).Count; Time=[DateTime]::UtcNow.ToString('o') }) | ConvertTo-Json -Compress)
    }
    $bytes = 0L
    $files = 0L
    foreach ($entry in $record.Entries) {
        foreach ($item in $entry.Inventory.Values) {
            if (-not $item.Directory) { $bytes += [long]$item.Bytes; $files++ }
        }
    }
    if ($bytes -ne 13630973746L -or $files -ne 9191L) { throw 'Fixture size/count differs from the reviewed proposal.' }
    $record.Bytes = $bytes
    $record.Files = $files
    $record.SourceRootsStillPresent = @($names | ForEach-Object { Test-Path -LiteralPath (Join-Path $sourceRoot $_) })
    if ($record.SourceRootsStillPresent -contains $false) { throw 'Source root missing after copy.' }
    Assert-Idle
    $vhd = Get-Item -LiteralPath 'D:\FusionRehearsal\Ubuntu\ext4.vhdx'
    $record.ProtectedVhdAfter = [ordered]@{ Length=$vhd.Length; ModifiedUtcTicks=$vhd.LastWriteTimeUtc.Ticks }
    if ($record.ProtectedVhdBefore.Length -ne $record.ProtectedVhdAfter.Length -or $record.ProtectedVhdBefore.ModifiedUtcTicks -ne $record.ProtectedVhdAfter.ModifiedUtcTicks) { throw 'Protected VHD changed during archive.' }
    $record.OtherRootsAfter = @(Get-ChildItem -LiteralPath $sourceRoot -Force | Sort-Object Name | ForEach-Object { $_.Name })
    if (($record.OtherRootsBefore -join '|') -cne ($record.OtherRootsAfter -join '|')) { throw 'Source root names changed.' }
    $record.Completed = $true
    $record.Finished = [DateTime]::UtcNow.ToString('o')
    $record.DFreeAfter = (Get-PSDrive D).Free
    $record.WFreeAfter = (Get-PSDrive W).Free
    Save-Record 'copy.json' $record
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'copy.json') -Destination (Join-Path $archiveRoot 'copy.json')
    if ((Get-Digest (Join-Path $PSScriptRoot 'copy.json')) -cne (Get-Digest (Join-Path $archiveRoot 'copy.json'))) { throw 'Final record mismatch.' }
    Write-Output (([ordered]@{ Completed='CopyOnly'; Bytes=$bytes; Files=$files; RemovedSources=0 }) | ConvertTo-Json -Compress)
} catch {
    Save-Record 'copy-failure.json' ([ordered]@{ Time=[DateTime]::UtcNow.ToString('o'); Error=$_.ToString(); Stack=$_.ScriptStackTrace })
    throw
} finally {
    foreach ($handle in $locks) { $handle.Dispose() }
}
