param([string]$RunName = 'recovery-node-v2')
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
if ($RunName -notmatch '^recovery-node-v[0-9]+$') { throw 'Unexpected run name' }
$root = Join-Path $workspace "tmp/$RunName"
$source = Join-Path $workspace 'tmp/preserved-head-state'
$manifest = Join-Path $workspace 'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'
$manifestHash = 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
$binary = Join-Path $workspace 'tmp/recovery-construction-tests.exe'
if (Test-Path -LiteralPath $root) { throw 'Run root already exists' }
if ((Get-PSDrive C).Free -lt 55GB) { throw 'Insufficient C: reserve' }
if ((Get-FileHash -LiteralPath $manifest).Hash.ToLowerInvariant() -ne $manifestHash) { throw 'Manifest mismatch' }
$entries = foreach ($line in [IO.File]::ReadAllLines($manifest)) {
    if ($line -notmatch '^([0-9a-f]{64})  \./(.+)$') { throw 'Malformed manifest' }
    [pscustomobject]@{ Hash = $Matches[1]; Path = $Matches[2] }
}
if ($entries.Count -ne 230 -or @(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 230) { throw 'Source inventory mismatch' }
New-Item -ItemType Directory -Path $root | Out-Null
Copy-Item -LiteralPath (Join-Path $workspace 'tmp/guarded-recovery-blocks') -Destination (Join-Path $root 'guarded-recovery-blocks') -Recurse
$env:FUSION_RESTART_HANDOVER_BLOCKS = Join-Path $root 'guarded-recovery-blocks'
$env:FUSION_RESTART_CHAINDATA = ''
$env:GOMAXPROCS = '2'
Push-Location (Join-Path $workspace 'tests/restart')
try {
    foreach ($role in @('backup', 'donation')) {
        $target = Join-Path $root "guarded-recovery-$role"
        New-Item -ItemType Directory -Path $target | Out-Null
        foreach ($entry in $entries) {
            $original = Join-Path $source $entry.Path
            if ((Get-FileHash -LiteralPath $original).Hash.ToLowerInvariant() -ne $entry.Hash) { throw 'Source mismatch' }
            $destination = Join-Path $target $entry.Path
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
            Copy-Item -LiteralPath $original -Destination $destination
            if ((Get-FileHash -LiteralPath $destination).Hash.ToLowerInvariant() -ne $entry.Hash) { throw 'Copy mismatch' }
        }
        $proof = @{ Source = $source; ManifestSHA256 = $manifestHash; Files = $entries.Count } | ConvertTo-Json
        [IO.File]::WriteAllText((Join-Path $target 'copy-verified.json'), $proof, [Text.UTF8Encoding]::new($false))
        $env:FUSION_RESTART_HANDOVER_DIR = $target
        $env:FUSION_RESTART_HANDOVER_MODE = 'prepare'
        & $binary '-test.run=^TestFullStateHandover$' '-test.v' '-test.timeout=5m' > (Join-Path $PSScriptRoot "$RunName-$role-prepare.txt") 2>&1
        if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
    }
} finally { Pop-Location }
