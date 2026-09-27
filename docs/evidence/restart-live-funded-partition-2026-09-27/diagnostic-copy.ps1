$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$source = 'D:\FusionRehearsal\live-funded-partition-2026-09-27'
$destination = 'D:\FusionRehearsal\live-funded-partition-2026-09-27-admission'
$evidence = Join-Path $workspace 'docs\evidence\restart-live-funded-partition-2026-09-27'
if (Test-Path -LiteralPath $destination) { throw 'Destination exists; preserve it.' }
$before = (Get-PSDrive D).Free
if ($before -lt 55GB) { throw 'Preserve host reserve.' }
$files = Get-ChildItem -LiteralPath (Join-Path $source 'verifier') -File -Recurse
$hashes = [ordered]@{}
$bytes = 0L
foreach ($file in $files) {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected source link.' }
    $relative = $file.FullName.Substring($source.Length + 1)
    $target = Join-Path $destination $relative
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    Copy-Item -LiteralPath $file.FullName -Destination $target
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) { throw "Copy mismatch: $relative" }
    $hashes[$relative.Replace('\', '/')] = $hash
    $bytes += $file.Length
}
foreach ($relative in $hashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $source $relative) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hashes[$relative]) { throw "Source changed: $relative" }
}
$encoding = [Text.UTF8Encoding]::new($false)
$audit = [IO.File]::ReadAllText((Join-Path $source 'cold-audit.json'), $encoding) | ConvertFrom-Json
$original = [IO.File]::ReadAllBytes((Join-Path $source 'repair/original-16.rlp'))
$inputRecord = [ordered]@{ Header=$audit.Heads[1]; Saved='0x' + [BitConverter]::ToString($original).Replace('-', '').ToLowerInvariant() }
[IO.File]::WriteAllText((Join-Path $destination 'diagnostic-saved-producer.json'), ($inputRecord | ConvertTo-Json -Depth 10) + "`n", $encoding)
[IO.File]::WriteAllText((Join-Path $evidence 'diagnostic-source-SHA256.json'), ($hashes | ConvertTo-Json -Depth 5) + "`n", $encoding)
$proof = [ordered]@{ Source=$source; Target=$destination; Files=$files.Count; Bytes=$bytes; FreeBytesBefore=$before; FreeBytesAfter=(Get-PSDrive D).Free; SourceUnchanged=$true }
[IO.File]::WriteAllText((Join-Path $evidence 'diagnostic-copy-capacity.json'), ($proof | ConvertTo-Json) + "`n", $encoding)
$proof | ConvertTo-Json
