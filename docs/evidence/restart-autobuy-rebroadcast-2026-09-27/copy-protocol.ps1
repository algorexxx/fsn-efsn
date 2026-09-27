$ErrorActionPreference = 'Stop'
$workspace = 'C:\Users\Peter\Documents\CODING\fsn-efsn'
$proof = Get-Content -LiteralPath (Join-Path $workspace 'docs\evidence\restart-peer-purchase-retry-2026-09-27\source-copy.json') -Raw -Encoding utf8 | ConvertFrom-Json
$proof.Target = 'D:\FusionRehearsal\autobuy-rebroadcast-2026-09-27\peer-purchase-retry-2026-09-27\receiver'
if (Test-Path -LiteralPath $proof.Target) { throw 'Destination already exists; preserve it.' }
if ((Get-PSDrive D).Free -lt 5GB) { throw 'Insufficient D: capacity.' }
foreach ($entry in $proof.SHA256.PSObject.Properties) {
    $source = Join-Path $proof.Source $entry.Name
    $target = Join-Path $proof.Target $entry.Name
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) { throw "Retained source changed: $source" }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) { throw "Copy differs: $target" }
}
$encoding = [Text.UTF8Encoding]::new($false)
$json = ($proof | ConvertTo-Json -Depth 5) + "`n"
[IO.File]::WriteAllText((Join-Path $proof.Target 'peer-retry-copy.json'), $json, $encoding)
[IO.File]::WriteAllText((Join-Path $workspace 'docs\evidence\restart-autobuy-rebroadcast-2026-09-27\protocol-source-copy.json'), $json, $encoding)
Write-Output "Verified $($proof.Files) files, $($proof.Bytes) bytes at $($proof.Target)"
