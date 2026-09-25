$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$report = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'source-manifest-match.json') -Encoding UTF8 | ConvertFrom-Json
$package = 'W:/FusionRestart/restore-rehearsal-2026-09-24/package'
$parent = 'W:/FusionRestart/restore-rehearsal-2026-09-24/restored-node'
$target = Join-Path $parent 'efsn'
if (Test-Path -LiteralPath $parent) { throw 'Restore parent already exists' }
if ((Get-PSDrive W).Free -lt (220GB)) { throw 'Insufficient restore capacity and reserve' }
if ((Get-FileHash -LiteralPath (Join-Path $package 'manifest.json')).Hash.ToLowerInvariant() -ne $report.manifest_sha256) { throw 'Reviewed package manifest changed' }
New-Item -ItemType Directory -Path $parent -ErrorAction Stop | Out-Null
& py -3 (Join-Path $workspace 'tests/restart/snapshot_package.py') restore --source $package --destination $target --manifest-sha256 $report.manifest_sha256 --stop 'W:/FusionRestart/restore-rehearsal-2026-09-24/STOP-RESTORE' 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'restore.txt')
$result = $LASTEXITCODE
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'restore-exit-code.txt'), [string]$result, [Text.UTF8Encoding]::new($false))
if ($result -ne 0) { throw 'Restore incomplete; do not start its database' }
Copy-Item -LiteralPath (Join-Path $target 'restored.json') -Destination (Join-Path $PSScriptRoot 'restored.json') -ErrorAction Stop
