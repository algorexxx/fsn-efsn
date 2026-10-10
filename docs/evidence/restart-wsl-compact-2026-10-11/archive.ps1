$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$source = 'D:\FusionRehearsal\Ubuntu\ext4.vhdx'
$sourceRoot = 'D:\FusionRehearsal'
$archiveRoot = 'W:\FusionRestart\rehearsal-vhd-before-compact-2026-10-11'
$archive = Join-Path $archiveRoot 'ext4.vhdx'
$staging = $archive + '.incomplete'
$encoding = [Text.UTF8Encoding]::new($false)
$timer = [Diagnostics.Stopwatch]::StartNew()
$deadlineSeconds = 36000
$lastProgress = -60.0
$sourceStream = $null
$archiveStream = $null
$record = [ordered]@{ Mode='ColdVhdCopyOnly'; Started=[DateTime]::UtcNow.ToString('o'); Source=$source; Archive=$archive; Commands=@(); Completed=$false; RemovedSources=@() }

function Save-Record($name, $value) {
    $path = Join-Path $PSScriptRoot $name
    if (Test-Path -LiteralPath $path) { throw "Preserve existing record: $name" }
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 12) + "`n", $encoding)
}

function Assert-Path($path, $root) {
    $full = [IO.Path]::GetFullPath($path)
    if ($full -cne $path -or -not $full.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Out-of-scope path: $path" }
    $current = Get-Item -LiteralPath $path -Force
    while ($null -ne $current -and $current.FullName.Length -ge $root.Length) {
        if ($current.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $path" }
        $current = if ($current -is [IO.DirectoryInfo]) { $current.Parent } else { $current.Directory }
    }
}

function Assert-Idle {
    if ($timer.Elapsed.TotalSeconds -gt $deadlineSeconds) { throw 'Ten-hour copy/verification limit exceeded.' }
    $running = ((& wsl.exe --list --running --quiet) -join "`n").Replace([string][char]0, '')
    if ($LASTEXITCODE -ne 0 -or $running.Contains('FusionRehearsal')) { throw 'FusionRehearsal must remain stopped.' }
    $active = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(efsn|replay-tests|restart-tests|observer)$' })
    if ($active.Count) { throw 'A native rehearsal executable is running.' }
    if ((Get-PSDrive W).DisplayRoot -cne '\\192.168.1.250\mnemosyne1') { throw 'Unexpected W: mapping.' }
    if ((Get-PSDrive C).Free -lt 5GB -or (Get-PSDrive W).Free -lt 100GB) { throw 'Output-volume reserve failed.' }
}

function Save-Progress($phase, [long]$bytes, [long]$total, [bool]$force) {
    if (-not $force -and $timer.Elapsed.TotalSeconds - $script:lastProgress -lt 60) { return }
    Assert-Idle
    $script:lastProgress = $timer.Elapsed.TotalSeconds
    $value = [ordered]@{ Phase=$phase; Updated=[DateTime]::UtcNow.ToString('o'); Bytes=$bytes; TotalBytes=$total; ElapsedSeconds=$timer.Elapsed.TotalSeconds; WFree=(Get-PSDrive W).Free; DFree=(Get-PSDrive D).Free; SourceReadLockHeld=($null -ne $sourceStream); Completed=$false }
    $temp = Join-Path $PSScriptRoot 'archive-progress.next.json'
    $path = Join-Path $PSScriptRoot 'archive-progress.json'
    [IO.File]::WriteAllText($temp, ($value | ConvertTo-Json -Depth 6) + "`n", $encoding)
    [IO.File]::Move($temp, $path, $true)
    [Console]::WriteLine(($value | ConvertTo-Json -Compress))
}

function Read-StreamDigest($stream, $phase, [long]$total, $destination) {
    $hash = [Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
    $buffer = [byte[]]::new(8MB)
    $bytes = 0L
    $stream.Position = 0
    try {
        Save-Progress $phase $bytes $total $true
        while (($count = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            if ($timer.Elapsed.TotalSeconds -gt $deadlineSeconds) { throw 'Ten-hour copy/verification limit exceeded.' }
            $hash.AppendData($buffer, 0, $count)
            if ($null -ne $destination) { $destination.Write($buffer, 0, $count) }
            $bytes += $count
            Save-Progress $phase $bytes $total $false
        }
        if ($bytes -ne $total) { throw 'Complete file length differs from the source inventory.' }
        Save-Progress $phase $bytes $total $true
        return [Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant()
    } finally { $hash.Dispose() }
}

try {
    foreach ($line in [IO.File]::ReadAllLines((Join-Path $PSScriptRoot 'INPUT_SHA256SUMS'), $encoding)) {
        if ($line -notmatch '^([0-9a-f]{64})\s+(.+)$') { throw 'Malformed input manifest.' }
        if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $Matches[2]) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Matches[1]) { throw 'Changed archive input.' }
    }
    $prior = Join-Path (Split-Path $PSScriptRoot -Parent) 'restart-ticket-encoder-job-6300000-v3-2026-10-10'
    $completion = Get-Content -LiteralPath (Join-Path $prior 'completion.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $verification = Get-Content -LiteralPath (Join-Path $prior 'verification.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $completion.verified_pass -or $completion.exit -ne 0 -or -not $verification.pass -or $verification.end_height -ne 6300000) { throw 'Latest finite replay is not verified.' }
    $manifest = Join-Path $prior 'SHA256SUMS'
    if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'e99e6f4b516e9119f9ffc18a5ac1519ab613e96203ba395c971fba5f8ed83845') { throw 'Unexpected completed-evidence manifest.' }
    $entries = 0
    foreach ($line in [IO.File]::ReadAllLines($manifest, $encoding)) {
        if ($line -notmatch '^([0-9a-f]{64})\s+(.+)$') { throw 'Malformed completion manifest.' }
        $expected = $Matches[1]
        $file = [IO.Path]::GetFullPath((Join-Path $prior $Matches[2]))
        Assert-Path $file $prior
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected) { throw 'Changed completion evidence.' }
        $entries++
    }
    $record.EvidenceFilesVerified = $entries
    Assert-Idle
    Assert-Path $source $sourceRoot
    $image = Get-DiskImage -ImagePath $source -ErrorAction Stop
    if ($image.Attached -or $image.Size -ne 236223201280L) { throw 'Expected detached 220 GiB rehearsal disk.' }
    $record.VirtualDiskBytes = [long]$image.Size
    $sourceStream = [IO.File]::Open($source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    $item = Get-Item -LiteralPath $source -Force
    $record.SourceBefore = [ordered]@{ Length=$item.Length; ModifiedUtcTicks=$item.LastWriteTimeUtc.Ticks; Attributes=[int]$item.Attributes }
    if ($item.Length -ne 211278626816L -or $sourceStream.Length -ne $item.Length) { throw 'Cold VHD size differs from reviewed scope.' }
    $record.SourceReadLockHeld = $true
    $record.ScriptSHA256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $record.DFreeBefore = (Get-PSDrive D).Free
    $record.WFreeBefore = (Get-PSDrive W).Free
    if ($record.WFreeBefore -le $item.Length + 100GB) { throw 'Archive and reserve do not fit W:.' }
    if (Test-Path -LiteralPath $archiveRoot) { throw 'Archive destination already exists.' }
    [IO.Directory]::CreateDirectory($archiveRoot) | Out-Null
    Assert-Path $archiveRoot 'W:\FusionRestart'
    Save-Record 'archive-started.json' $record
    $archiveStream = [IO.File]::Open($staging, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::Read)
    $copiedDigest = Read-StreamDigest $sourceStream 'copy-and-source-sha256' $item.Length $archiveStream
    $archiveStream.Flush($true)
    $record.CopySHA256 = $copiedDigest
    $sourceDigest = Read-StreamDigest $sourceStream 'source-reverification' $item.Length $null
    if ($sourceDigest -cne $copiedDigest) { throw 'Source bytes changed during copy.' }
    $destinationDigest = Read-StreamDigest $archiveStream 'archive-reverification' $item.Length $null
    if ($destinationDigest -cne $copiedDigest) { throw 'Archive bytes differ from the source.' }
    $archiveStream.Dispose()
    $archiveStream = $null
    Assert-Idle
    $item = Get-Item -LiteralPath $source -Force
    $record.SourceAfter = [ordered]@{ Length=$item.Length; ModifiedUtcTicks=$item.LastWriteTimeUtc.Ticks; Attributes=[int]$item.Attributes }
    if (($record.SourceBefore | ConvertTo-Json -Compress) -cne ($record.SourceAfter | ConvertTo-Json -Compress)) { throw 'Cold source metadata changed.' }
    Assert-Path $staging $archiveRoot
    if ([IO.Path]::GetFullPath($archive) -cne $archive -or -not $archive.StartsWith($archiveRoot+'\', [StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $archive)) { throw 'Unsafe archive final path.' }
    Move-Item -LiteralPath $staging -Destination $archive
    Assert-Path $archive $archiveRoot
    [IO.File]::SetLastWriteTimeUtc($archive, [DateTime]::new($record.SourceBefore.ModifiedUtcTicks, [DateTimeKind]::Utc))
    if ((Get-Item -LiteralPath $archive).Length -ne $record.SourceBefore.Length) { throw 'Final archive length changed.' }
    if ((Get-DiskImage -ImagePath $source -ErrorAction Stop).Attached) { throw 'Source disk attached during copy.' }
    $record.SourceReverifiedSHA256 = $sourceDigest
    $record.ArchiveReverifiedSHA256 = $destinationDigest
    $record.WFreeAfter = (Get-PSDrive W).Free
    $record.DFreeAfter = (Get-PSDrive D).Free
    $record.Completed = $true
    $record.Finished = [DateTime]::UtcNow.ToString('o')
    Save-Record 'archive.json' $record
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'archive.json') -Destination (Join-Path $archiveRoot 'archive.json')
    if ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'archive.json')).Hash -cne (Get-FileHash -LiteralPath (Join-Path $archiveRoot 'archive.json')).Hash) { throw 'Archive record mismatch.' }
    Write-Output ($record | ConvertTo-Json -Depth 12)
} catch {
    Save-Record 'archive-failure.json' ([ordered]@{ Time=[DateTime]::UtcNow.ToString('o'); Error=$_.ToString(); Stack=$_.ScriptStackTrace; Completed=$false })
    throw
} finally {
    if ($null -ne $archiveStream) { $archiveStream.Dispose() }
    if ($null -ne $sourceStream) { $sourceStream.Dispose() }
}
