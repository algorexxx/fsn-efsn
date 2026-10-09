$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$sourceRoot = 'D:\FusionRehearsal'
$archiveRoot = 'W:\FusionRestart\old-tests-archive-v2-2026-10-09'
$repository = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$names = @('autobuy-rebroadcast-2026-09-27', 'recovered-buyer-restart-2026-09-27', 'abandonment-repair-2026-09-27', 'funded-gap-2026-09-27', 'equal-weight-pause-2026-09-27', 'stale-intent-ordered-2026-09-27', 'equal-weight-fresh-2026-09-27', 'live-funded-partition-2026-09-27', 'expired-nonce-neutralization-2026-09-27', 'paused-purchases-2026-09-27')
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


$record = [ordered]@{ Mode='VerifyExistingCopies'; Started=[DateTime]::UtcNow.ToString('o'); ScriptSHA256=(Get-Digest $PSCommandPath); OriginalCopyScriptSHA256=(Get-Digest (Join-Path $PSScriptRoot 'archive.ps1')); OriginalCopyFailureSHA256=(Get-Digest (Join-Path $PSScriptRoot 'copy-failure.json')); DFreeBefore=(Get-PSDrive D).Free; WFreeBefore=(Get-PSDrive W).Free; Entries=@(); Bytes=0L; Completed=$false }
try {
    Assert-Idle
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'copy.json')) { throw 'Copy verification record exists.' }
    Assert-Path $archiveRoot 'W:\FusionRestart'
    foreach ($name in $names) {
        $source = Join-Path $sourceRoot $name
        Assert-Path $source $sourceRoot
        foreach ($file in @(Get-ChildItem -LiteralPath $source -Recurse -File -Force | Where-Object { $_.Name -eq 'LOCK' -or $_.Name -like '*.run.lock' })) {
            Assert-Path $file.FullName $source
            $locks.Add([IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read))
        }
    }
    $record.LockHandles = $locks.Count
    foreach ($name in $names) {
        Assert-Idle
        $source = Join-Path $sourceRoot $name
        $destination = Join-Path $archiveRoot $name
        Assert-Path $destination $archiveRoot
        $evidence = Assert-Evidence $name
        $inventory = Get-Inventory $source
        foreach ($relative in $inventory.Keys) {
            if (-not $inventory[$relative].Directory) {
                $inventory[$relative].SHA256 = Get-Digest (Join-Path $source $relative)
                $record.Bytes += [long]$inventory[$relative].Bytes
            }
        }
        Assert-Inventory $source $inventory $true
        Assert-Inventory $destination $inventory $false
        $entry = [ordered]@{ Name=$name; Source=$source; Archive=$destination; Evidence=$evidence; Inventory=$inventory; Verified=[DateTime]::UtcNow.ToString('o') }
        Save-Record ($name+'.manifest.json') $entry
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot ($name+'.manifest.json')) -Destination (Join-Path $archiveRoot ($name+'.manifest.json'))
        if ((Get-Digest (Join-Path $PSScriptRoot ($name+'.manifest.json'))) -cne (Get-Digest (Join-Path $archiveRoot ($name+'.manifest.json')))) { throw 'Per-directory manifest mismatch.' }
        $record.Entries += $entry
        Write-Output (([ordered]@{ Verified=$name; Files=@($inventory.Values | Where-Object { -not $_.Directory }).Count; Time=[DateTime]::UtcNow.ToString('o') }) | ConvertTo-Json -Compress)
    }
    if ($record.Bytes -ne 12382043962) { throw 'Unexpected archived byte total.' }
    $record.Completed = $true
    $record.Finished = [DateTime]::UtcNow.ToString('o')
    $record.DFreeAfter = (Get-PSDrive D).Free
    $record.WFreeAfter = (Get-PSDrive W).Free
    Save-Record 'copy.json' $record
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'copy.json') -Destination (Join-Path $archiveRoot 'copy.json')
    if ((Get-Digest (Join-Path $PSScriptRoot 'copy.json')) -cne (Get-Digest (Join-Path $archiveRoot 'copy.json'))) { throw 'Final record mismatch.' }
    Write-Output (([ordered]@{ Completed=$true; Bytes=$record.Bytes; DFree=$record.DFreeAfter }) | ConvertTo-Json -Compress)
} catch {
    Save-Record 'copy-recovery-failure.json' ([ordered]@{ Time=[DateTime]::UtcNow.ToString('o'); Error=$_.ToString(); Stack=$_.ScriptStackTrace })
    throw
} finally {
    foreach ($handle in $locks) { $handle.Dispose() }
}
