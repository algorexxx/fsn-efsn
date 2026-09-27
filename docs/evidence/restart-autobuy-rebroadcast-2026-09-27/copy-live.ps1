$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$source = Join-Path $workspace 'tmp\full-state-peer-reconnect-2026-09-27'
$destination = 'D:\FusionRehearsal\autobuy-rebroadcast-2026-09-27'
$evidence = Join-Path $workspace 'docs\evidence\restart-autobuy-rebroadcast-2026-09-27'
if (Test-Path -LiteralPath $destination) { throw 'Destination already exists; preserve it.' }
$before = (Get-PSDrive D).Free
if ($before -lt 5GB) { throw 'Insufficient D: capacity.' }
$files = @()
foreach ($role in @('producer', 'verifier')) {
    $files += Get-ChildItem -LiteralPath (Join-Path $source $role) -File -Recurse
}
foreach ($name in @('blocks\block-03.json', 'diagnostic-saved-producer.json', 'diagnostic-saved-verifier.json', 'funding-recovery.json')) {
    $files += Get-Item -LiteralPath (Join-Path $source $name)
}
$hashes = [ordered]@{}
$bytes = 0L
foreach ($file in $files) {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected source link.' }
    $relative = $file.FullName.Substring($source.Length + 1)
    $target = Join-Path $destination $relative
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
[IO.File]::WriteAllText((Join-Path $evidence 'source-copies-SHA256.json'), ($hashes | ConvertTo-Json -Depth 5) + "`n", $encoding)
$proof = [ordered]@{ Source=$source; Target=$destination; Files=$files.Count; Bytes=$bytes; FreeBytesBefore=$before; FreeBytesAfter=(Get-PSDrive D).Free; SourceUnchanged=$true }
[IO.File]::WriteAllText((Join-Path $evidence 'copy-capacity.json'), ($proof | ConvertTo-Json) + "`n", $encoding)
$proof | ConvertTo-Json
