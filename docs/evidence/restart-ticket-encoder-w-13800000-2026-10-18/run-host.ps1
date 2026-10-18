$ErrorActionPreference = 'Stop'
$bundle = $PSScriptRoot
$work = 'C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/replay-w-13800000-2026-10-18'
if (Test-Path -LiteralPath $work) { throw 'Preserve existing host job records' }
$mapping = Get-SmbMapping -LocalPath 'W:'
if ($mapping.RemotePath -ne '\\192.168.1.250\mnemosyne1' -or $mapping.Status -ne 'OK') { throw 'Unexpected W: mapping' }
$inputHash = (Get-FileHash -LiteralPath (Join-Path $bundle 'inputs/SHA256SUMS') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($inputHash -ne '0b0c9b6aa76c800f3128444cd6a3d5f6d85d4fecd29a6d2047b0330a992b15a3') { throw 'Input manifest identity differs' }
foreach ($line in Get-Content -LiteralPath (Join-Path $bundle 'inputs/SHA256SUMS') -Encoding UTF8) {
    $parts = $line -split '\s+', 2
    $actual = (Get-FileHash -LiteralPath (Join-Path $bundle ('inputs/' + $parts[1])) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $parts[0]) { throw ('Input changed: ' + $parts[1]) }
}
$priorReport = Join-Path (Split-Path $bundle -Parent) 'restart-ticket-encoder-w-13500000-2026-10-17/REPORT_SHA256SUMS'
if ((Get-FileHash -LiteralPath $priorReport -Algorithm SHA256).Hash.ToLowerInvariant() -ne '39e0c643b5717634de2b4f04c1ee47a37a9e75967185d8f959e3fa52aa151e72') { throw 'Prior outer report manifest changed' }
foreach ($line in Get-Content -LiteralPath $priorReport -Encoding UTF8) {
    $parts = $line -split '\s+', 2
    $actual = (Get-FileHash -LiteralPath (Join-Path (Split-Path $priorReport -Parent) $parts[1]) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $parts[0]) { throw ('Prior report changed: ' + $parts[1]) }
}
$null = New-Item -ItemType Directory -Path $work
$start = [DateTimeOffset]::UtcNow.ToString('o')
$argv = @('-d','FusionRehearsal','-u','root','--','timeout','--kill-after=20s','28800s','python3','-B','/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-ticket-encoder-w-13800000-2026-10-18/inputs/replay_image.py')
[ordered]@{ started=$start; argv=$argv; dispatcher_pid=$PID; input_manifest_sha256=$inputHash } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $work 'dispatch.json') -Encoding utf8
& wsl.exe @argv 1> (Join-Path $work 'stdout.txt') 2> (Join-Path $work 'stderr.txt')
$code = $LASTEXITCODE
[ordered]@{ started=$start; finished=[DateTimeOffset]::UtcNow.ToString('o'); argv=$argv; exit=$code } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $work 'host-run.json') -Encoding utf8
exit $code
