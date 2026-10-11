$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$source = 'D:\FusionRehearsal\Ubuntu\ext4.vhdx'
$rollback = '\\192.168.1.250\mnemosyne1\FusionRestart\rehearsal-vhd-before-compact-2026-10-11\ext4.vhdx'
$encoding = [Text.UTF8Encoding]::new($false)
$archiveStream = $null
$record = [ordered]@{ Started=[DateTime]::UtcNow.ToString('o'); Source=$source; Rollback=$rollback; Completed=$false; Mode='One native detached VHD compaction; no shrink or deletion' }

function Save-Record($name, $value) {
    $path = Join-Path $PSScriptRoot $name
    if (Test-Path -LiteralPath $path) { throw "Preserve existing record: $name" }
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 10) + "`n", $encoding)
}

function Assert-Cold {
    $running = ((& wsl.exe --list --running --quiet) -join "`n").Replace([string][char]0, '')
    if ($LASTEXITCODE -ne 0 -or $running.Contains('FusionRehearsal')) { throw 'Rehearsal must be stopped.' }
    $image = Get-DiskImage -ImagePath $source -ErrorAction Stop
    if ($image.Attached -or $image.Size -ne 236223201280L) { throw 'Expected detached 220 GiB disk.' }
    if ((Get-PSDrive D).Free -lt 50GB -or (Get-PSDrive C).Free -lt 5GB) { throw 'Storage reserve failed.' }
}

try {
    if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'native-started.json')) { throw 'Native compaction already attempted.' }
    $principal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Windows administrator elevation is required.' }
    foreach ($name in @('ARCHIVE_OUTPUT_SHA256SUMS','BEFORE_OUTPUT_SHA256SUMS','TRIM_OUTPUT_SHA256SUMS','NATIVE_INPUT_SHA256SUMS')) {
        foreach ($line in [IO.File]::ReadAllLines((Join-Path $PSScriptRoot $name), $encoding)) {
            if ($line -notmatch '^([0-9a-f]{64})\s+(.+)$') { throw 'Malformed preservation manifest.' }
            $expected = $Matches[1]
            $path = Join-Path $PSScriptRoot $Matches[2]
            if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected) { throw "Changed prerequisite: $path" }
        }
    }
    $before = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'before/verification.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $exitRecord = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'before-completion.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $trim = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'trim.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $before.pass -or $exitRecord.exit -ne 0 -or -not $trim.pass) { throw 'Before checks and unused-block trim must pass.' }
    $archive = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'archive.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $archive.Completed -or $archive.CopySHA256 -cne $archive.SourceReverifiedSHA256 -or $archive.CopySHA256 -cne $archive.ArchiveReverifiedSHA256) { throw 'Unverified rollback image.' }
    $receipt = Join-Path (Split-Path $rollback -Parent) 'archive.json'
    if ((Get-FileHash -LiteralPath $receipt).Hash -cne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'archive.json')).Hash) { throw 'Rollback receipt changed.' }
    foreach ($path in @($source,$rollback)) {
        if ([IO.Path]::GetFullPath($path) -cne $path) { throw 'Non-canonical disk path.' }
        $cursor = Get-Item -LiteralPath $path -Force
        while ($null -ne $cursor) {
            if ($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point in disk path.' }
            $cursor = if ($cursor -is [IO.DirectoryInfo]) { $cursor.Parent } else { $cursor.Directory }
        }
    }
    $archiveStream = [IO.File]::Open($rollback, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    if ($archiveStream.Length -ne 211278626816L) { throw 'Rollback length differs.' }
    Assert-Cold
    $record.SourceLengthBefore = (Get-Item -LiteralPath $source).Length
    $record.DFreeBefore = (Get-PSDrive D).Free
    $record.ScriptSHA256 = (Get-FileHash -LiteralPath $PSCommandPath).Hash.ToLowerInvariant()
    Save-Record 'native-started.json' $record
    $help = & "$env:SystemRoot\System32\diskpart.exe" /s (Join-Path $PSScriptRoot 'diskpart-help.txt') 2>&1
    $record.HelpExit = $LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'diskpart-help-output.txt'), ($help -join "`n") + "`n", $encoding)
    if ($record.HelpExit -ne 0 -or ($help -join ' ') -notmatch 'COMPACT VDISK' -or ($help -join ' ') -notmatch 'read.only') { throw 'Installed DiskPart help did not qualify detached compaction.' }
    Start-Sleep -Seconds 15
    Assert-Cold
    $record.CompactionStarted = [DateTime]::UtcNow.ToString('o')
    $timer = [Diagnostics.Stopwatch]::StartNew()
    & "$env:SystemRoot\System32\diskpart.exe" /s (Join-Path $PSScriptRoot 'diskpart-compact.txt') 2>&1 | Out-File -LiteralPath (Join-Path $PSScriptRoot 'diskpart-compact-output.txt') -Encoding utf8
    $record.NativeExit = $LASTEXITCODE
    $record.ElapsedSeconds = $timer.Elapsed.TotalSeconds
    if ($record.NativeExit -ne 0) { throw 'Native compaction failed; preserve both disk states.' }
    $log = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'diskpart-compact-output.txt') -Raw -Encoding UTF8
    if ($log -notmatch 'successfully compacted') { throw 'Native output did not confirm completed compaction.' }
    Assert-Cold
    $record.SourceLengthAfter = (Get-Item -LiteralPath $source).Length
    $record.DFreeAfter = (Get-PSDrive D).Free
    $record.ReclaimedFileBytes = $record.SourceLengthBefore - $record.SourceLengthAfter
    $record.VirtualBytesAfter = [long](Get-DiskImage -ImagePath $source).Size
    $record.Completed = $true
    $record.Finished = [DateTime]::UtcNow.ToString('o')
    Save-Record 'native-completion.json' $record
} catch {
    $record.Error = $_.ToString()
    $record.Stack = $_.ScriptStackTrace
    $record.Finished = [DateTime]::UtcNow.ToString('o')
    Save-Record 'native-failure.json' $record
    throw
} finally {
    if ($null -ne $archiveStream) { $archiveStream.Dispose() }
}
