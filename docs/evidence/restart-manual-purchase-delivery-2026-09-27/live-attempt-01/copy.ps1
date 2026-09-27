param([ValidateSet('protocol', 'live')][string]$Phase)
$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$source = 'D:\FusionRehearsal\live-funded-partition-2026-09-27'
$destination = "D:\FusionRehearsal\manual-purchase-$Phase-2026-09-27"
if ($Phase -eq 'protocol') { $destination += '-attempt-02' }
$evidence = Join-Path $workspace 'docs\evidence\restart-manual-purchase-delivery-2026-09-27'
if (Test-Path -LiteralPath $destination) { throw 'Destination exists; preserve it.' }
$before = (Get-PSDrive D).Free
if ($before -lt 55GB) { throw 'Preserve host reserve.' }
$roles = @('verifier')
if ($Phase -eq 'live') { $roles = @('producer', 'verifier', 'audit-producer', 'repair') }
$files = @()
foreach ($role in $roles) { $files += Get-ChildItem -LiteralPath (Join-Path $source $role) -File -Recurse }
if ($Phase -eq 'live') { $files += Get-Item -LiteralPath (Join-Path $source 'funding-plan.json') }
$hashes = [ordered]@{}
$bytes = 0L
foreach ($file in $files) {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected source link.' }
    $relative = $file.FullName.Substring($source.Length + 1)
    $targetRelative = $relative
    if ($relative.StartsWith('audit-producer\')) { $targetRelative = 'retained-blocks\' + $relative.Substring('audit-producer\'.Length) }
    $target = Join-Path $destination $targetRelative
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
[IO.File]::WriteAllText((Join-Path $evidence "$Phase-source-SHA256.json"), ($hashes | ConvertTo-Json -Depth 5) + "`n", $encoding)
$proof = [ordered]@{ Source=$source; Target=$destination; Files=$files.Count; Bytes=$bytes; FreeBytesBefore=$before; FreeBytesAfter=(Get-PSDrive D).Free; SourceUnchanged=$true }
$proofText = ($proof | ConvertTo-Json) + "`n"
[IO.File]::WriteAllText((Join-Path $destination 'copy-capacity.json'), $proofText, $encoding)
[IO.File]::WriteAllText((Join-Path $evidence "$Phase-copy-capacity.json"), $proofText, $encoding)
$proof | ConvertTo-Json
