$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$source = Join-Path $workspace 'tmp/preserved-head-state'
$manifest = Join-Path $workspace 'docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS'
$manifestHash = 'a6c86fc58a9f7b482a02b787a337d600e32a447551e45dbe40d210b498341bbf'
$binary = Join-Path $workspace 'tmp/full-state-handover-v2-tests.exe'
$bridge = Join-Path $workspace 'tmp/full-state-handover-blocks'
$utf8 = [Text.UTF8Encoding]::new($false)
if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifestHash) { throw 'Unexpected artifact manifest' }
if ((Get-PSDrive C).Free -lt 55GB) { throw 'Insufficient C: reserve for rehearsal copies' }
if (Test-Path -LiteralPath $bridge) { throw 'Refusing existing block artifact directory' }
$entries = foreach ($line in [IO.File]::ReadAllLines($manifest)) {
    if ($line -notmatch '^([0-9a-f]{64})  \./(.+)$') { throw 'Malformed manifest' }
    [pscustomobject]@{ Hash = $Matches[1]; Path = $Matches[2] }
}
if ($entries.Count -ne 230 -or @(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 230) { throw 'Unexpected source file inventory' }
foreach ($entry in $entries) {
    if ((Get-FileHash -LiteralPath (Join-Path $source $entry.Path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Hash) { throw "Source mismatch: $($entry.Path)" }
}
foreach ($role in @('producer', 'verifier')) {
    $target = Join-Path $workspace "tmp/full-state-handover-v2-$role"
    if (Test-Path -LiteralPath $target) { throw "Refusing existing target: $target" }
    New-Item -ItemType Directory -Path $target | Out-Null
    foreach ($entry in $entries) {
        $destination = Join-Path $target $entry.Path
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
        Copy-Item -LiteralPath (Join-Path $source $entry.Path) -Destination $destination
        if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Hash) { throw "Copy mismatch: $destination" }
    }
    $proof = @{ Source = $source; ManifestSHA256 = $manifestHash; Files = $entries.Count } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $target 'copy-verified.json'), $proof, $utf8)
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot "$role-copy-verified.json"), $proof, $utf8)
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'windows-binary-sha256.txt'), (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant()+"`n", $utf8)
$env:GOMAXPROCS = '2'
$env:FUSION_RESTART_CHAINDATA = ''
$env:FUSION_RESTART_HANDOVER_BLOCKS = $bridge
Push-Location (Join-Path $workspace 'tests/restart')
try {
    foreach ($phase in @('producer:prepare', 'verifier:prepare', 'producer:produce', 'producer:runtime-first', 'producer:runtime-restart', 'verifier:import', 'producer:cold', 'verifier:cold')) {
        $role, $label = $phase.Split(':')
        $mode = $label.Split('-')[0]
        if ((Get-PSDrive C).Free -lt 50GB) { throw 'C: reserve reached' }
        $env:FUSION_RESTART_HANDOVER_DIR = Join-Path $workspace "tmp/full-state-handover-v2-$role"
        $env:FUSION_RESTART_HANDOVER_MODE = $mode
        [IO.File]::WriteAllText((Join-Path $PSScriptRoot "$role-$label-started.txt"), [DateTime]::UtcNow.ToString('o')+"`n", $utf8)
        & $binary '-test.run=^TestFullStateHandover$' '-test.v' '-test.timeout=20m' > (Join-Path $PSScriptRoot "$role-$label.txt") 2>&1
        $code = $LASTEXITCODE
        [IO.File]::WriteAllText((Join-Path $PSScriptRoot "$role-$label-exit-code.txt"), "$code`n", $utf8)
        Get-Content -LiteralPath (Join-Path $PSScriptRoot "$role-$label.txt") -Tail 5
        if ($code -ne 0) { throw "Full-state handover phase failed: $phase" }
    }
} finally { Pop-Location }
