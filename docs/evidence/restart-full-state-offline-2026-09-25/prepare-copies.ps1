param([Parameter(Mandatory = $true)][ValidateSet('windows', 'linux')][string]$Platform)
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$source = Join-Path $workspace 'tmp/preserved-head-state'
$manifest = Join-Path $workspace 'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'
$manifestHash = 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
$root = Join-Path $workspace "tmp/full-state-offline-$Platform-2026-09-25"
$utf8 = [Text.UTF8Encoding]::new($false)
if (Test-Path -LiteralPath $root) { throw "Refusing existing root: $root" }
if ((Get-PSDrive C).Free -lt 55GB) { throw 'Insufficient C: reserve' }
if ((Get-FileHash -LiteralPath $manifest).Hash.ToLowerInvariant() -ne $manifestHash) { throw 'Manifest mismatch' }
$entries = foreach ($line in [IO.File]::ReadAllLines($manifest)) {
    if ($line -notmatch '^([0-9a-f]{64})  \./(.+)$') { throw 'Malformed manifest' }
    [pscustomobject]@{ Hash = $Matches[1]; Path = $Matches[2] }
}
if ($entries.Count -ne 230 -or @(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 230) { throw 'Unexpected source inventory' }
$bytes = 0L
foreach ($entry in $entries) {
    $file = Join-Path $source $entry.Path
    if ((Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $entry.Hash) { throw 'Source mismatch' }
    $bytes += (Get-Item -LiteralPath $file).Length
}
$roles = @('reference', 'completion/working', 'completion/verifier', 'export/working', 'export/verifier', 'import/working', 'import/verifier', 'reservation/working', 'signature/working')
foreach ($role in $roles) {
    if ((Get-PSDrive C).Free -lt 50GB) { throw 'C: reserve reached' }
    $target = Join-Path $root $role
    New-Item -ItemType Directory -Path $target | Out-Null
    foreach ($entry in $entries) {
        $destination = Join-Path $target $entry.Path
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
        Copy-Item -LiteralPath (Join-Path $source $entry.Path) -Destination $destination
        if ((Get-FileHash -LiteralPath $destination).Hash.ToLowerInvariant() -ne $entry.Hash) { throw "Copy mismatch: $destination" }
    }
    $proof = @{ Source = $source; ManifestSHA256 = $manifestHash; Files = $entries.Count } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $target 'copy-verified.json'), $proof, $utf8)
    Write-Output "Verified $role : $($entries.Count) files, $bytes bytes"
}
Write-Output "Prepared $($roles.Count) fresh $Platform copies; C: free bytes $((Get-PSDrive C).Free)"
