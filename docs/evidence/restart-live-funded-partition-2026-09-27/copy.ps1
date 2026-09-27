$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$source = Join-Path $workspace 'tmp\full-state-participant-2026-09-26-attempt-03'
$destination = 'D:\FusionRehearsal\live-funded-partition-2026-09-27'
$evidence = Join-Path $workspace 'docs\evidence\restart-live-funded-partition-2026-09-27'
if (Test-Path -LiteralPath $destination) { throw 'Destination already exists; preserve it.' }
$before = (Get-PSDrive D).Free
if ($before -lt 55GB) { throw 'Preserve 50 GiB host reserve plus working capacity.' }
$files = @()
foreach ($role in @('producer', 'verifier', 'blocks')) {
    $files += Get-ChildItem -LiteralPath (Join-Path $source $role) -File -Recurse
}
$hashes = [ordered]@{}
$bytes = 0L
foreach ($file in $files) {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected source link.' }
    $relative = $file.FullName.Substring($source.Length + 1)
    $targetRelative = $relative
    if ($relative.StartsWith('blocks\')) { $targetRelative = 'retained-' + $relative }
    $target = Join-Path $destination $targetRelative
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    Copy-Item -LiteralPath $file.FullName -Destination $target
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) { throw "Copy hash mismatch: $relative" }
    $hashes[$relative.Replace('\', '/')] = $hash
    $bytes += $file.Length
}
foreach ($relative in $hashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $source $relative) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$relative]) { throw "Source changed: $relative" }
}
$encoding = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $evidence 'source-SHA256.json'), ($hashes | ConvertTo-Json -Depth 5) + "`n", $encoding)
$proof = [ordered]@{ Source=$source; Target=$destination; BlocksCopiedAs='retained-blocks'; Files=$files.Count; Bytes=$bytes; FreeBytesBefore=$before; FreeBytesAfter=(Get-PSDrive D).Free; SourceUnchanged=$true; BuildAndDatabaseHostDrive='D:' }
[IO.File]::WriteAllText((Join-Path $evidence 'copy-capacity.json'), ($proof | ConvertTo-Json) + "`n", $encoding)
$proof | ConvertTo-Json
