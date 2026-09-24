$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$source = Join-Path $workspace 'tmp/preserved-head-state'
$manifest = Join-Path $workspace 'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'
$manifestHash = 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
$binary = Join-Path $workspace 'tmp/recovery-construction-tests.exe'
$command = Join-Path $workspace 'tmp/fsn-recovery.exe'
$artifacts = Join-Path $workspace 'tmp/guarded-recovery-blocks'
$utf8 = [Text.UTF8Encoding]::new($false)
if ((Get-PSDrive C).Free -lt 55GB) { throw 'Insufficient C: reserve' }
if (Test-Path -LiteralPath $artifacts) { throw 'Artifact path already exists' }
if ((Get-FileHash -LiteralPath $manifest).Hash.ToLowerInvariant() -ne $manifestHash) { throw 'Manifest mismatch' }
$entries = foreach ($line in [IO.File]::ReadAllLines($manifest)) {
    if ($line -notmatch '^([0-9a-f]{64})  \./(.+)$') { throw 'Malformed manifest' }
    [pscustomobject]@{ Hash = $Matches[1]; Path = $Matches[2] }
}
if ($entries.Count -ne 230 -or @(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 230) { throw 'Unexpected source inventory' }
foreach ($entry in $entries) {
    if ((Get-FileHash -LiteralPath (Join-Path $source $entry.Path)).Hash.ToLowerInvariant() -ne $entry.Hash) { throw 'Source mismatch' }
}
New-Item -ItemType Directory -Path $artifacts | Out-Null
$env:GOMAXPROCS = '2'
$env:FUSION_RESTART_CHAINDATA = ''
$env:FUSION_RESTART_HANDOVER_BLOCKS = $artifacts
Push-Location (Join-Path $workspace 'tests/restart')
try {
    foreach ($role in @('constructor', 'backup', 'donation')) {
        $target = Join-Path $workspace "tmp/guarded-recovery-$role"
        if (Test-Path -LiteralPath $target) { throw "Refusing existing target: $target" }
        New-Item -ItemType Directory -Path $target | Out-Null
        foreach ($entry in $entries) {
            $destination = Join-Path $target $entry.Path
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
            Copy-Item -LiteralPath (Join-Path $source $entry.Path) -Destination $destination
            if ((Get-FileHash -LiteralPath $destination).Hash.ToLowerInvariant() -ne $entry.Hash) { throw "Copy mismatch: $destination" }
        }
        $proof = @{ Source = $source; ManifestSHA256 = $manifestHash; Files = $entries.Count } | ConvertTo-Json
        [IO.File]::WriteAllText((Join-Path $target 'copy-verified.json'), $proof, $utf8)
        $env:FUSION_RESTART_HANDOVER_DIR = $target
        $env:FUSION_RESTART_HANDOVER_MODE = 'prepare'
        & $binary '-test.run=^TestFullStateHandover$' '-test.v' '-test.timeout=5m' > (Join-Path $PSScriptRoot "$role-prepare.txt") 2>&1
        if ($LASTEXITCODE -ne 0) { throw "$role preparation failed" }
        Get-Content -LiteralPath (Join-Path $PSScriptRoot "$role-prepare.txt") -Tail 3
    }
    $env:FUSION_RESTART_HANDOVER_DIR = Join-Path $workspace 'tmp/guarded-recovery-constructor'
    foreach ($index in 1..3) {
        $prefix = Join-Path $artifacts ('recovery-{0:d2}' -f $index)
        $env:FUSION_RESTART_HANDOVER_MODE = 'plan'
        & $binary '-test.run=^TestFullStateRecoveryConstruction$' '-test.v' '-test.timeout=2m' > (Join-Path $PSScriptRoot "step-$index-plan.txt") 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Plan $index failed" }
        $db = Join-Path $env:FUSION_RESTART_HANDOVER_DIR 'chaindata'
        $before = @(Get-ChildItem -LiteralPath $db -Recurse -File | Sort-Object FullName | ForEach-Object { "$($_.FullName) $((Get-FileHash -LiteralPath $_.FullName).Hash)" })
        & $command -chaindata $db -plan "$prefix-plan.json" -purchase "$prefix-purchase.rlp" -out "$prefix-report.json" > (Join-Path $PSScriptRoot "step-$index-command.txt") 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Read-only command $index failed" }
        $after = @(Get-ChildItem -LiteralPath $db -Recurse -File | Sort-Object FullName | ForEach-Object { "$($_.FullName) $((Get-FileHash -LiteralPath $_.FullName).Hash)" })
        if (Compare-Object $before $after) { throw 'Read-only construction changed database files' }
        [IO.File]::WriteAllText((Join-Path $PSScriptRoot "step-$index-readonly.txt"), "All $($before.Count) database files unchanged by unsigned construction.`n", $utf8)
        $env:FUSION_RESTART_HANDOVER_MODE = 'produce'
        & $binary '-test.run=^TestFullStateRecoveryConstruction$' '-test.v' '-test.timeout=2m' > (Join-Path $PSScriptRoot "step-$index-produce.txt") 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Guarded production $index failed" }
        Get-Content -LiteralPath (Join-Path $PSScriptRoot "step-$index-produce.txt") -Tail 4
    }
} finally { Pop-Location }
