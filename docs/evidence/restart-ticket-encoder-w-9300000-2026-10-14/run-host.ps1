$ErrorActionPreference = 'Stop'
$bundle = $PSScriptRoot
$work = 'C:/Users/Peter/Documents/CODING/fsn-efsn/tmp/replay-w-9300000-2026-10-14'
if (Test-Path -LiteralPath $work) { throw 'Preserve existing host job records' }
$mapping = Get-SmbMapping -LocalPath 'W:'
if ($mapping.RemotePath -ne '\\192.168.1.250\mnemosyne1' -or $mapping.Status -ne 'OK') { throw 'Unexpected W: mapping' }
$inputHash = (Get-FileHash -LiteralPath (Join-Path $bundle 'inputs/SHA256SUMS') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($inputHash -ne 'd0df1e838cf33f2f711d7e91fff91579823ca0322f80de2816d94bc587ea003e') { throw 'Input manifest identity differs' }
foreach ($line in Get-Content -LiteralPath (Join-Path $bundle 'inputs/SHA256SUMS') -Encoding UTF8) {
    $parts = $line -split '\s+', 2
    $actual = (Get-FileHash -LiteralPath (Join-Path $bundle ('inputs/' + $parts[1])) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $parts[0]) { throw ('Input changed: ' + $parts[1]) }
}
$priorReport = Join-Path (Split-Path $bundle -Parent) 'restart-ticket-encoder-w-9000000-2026-10-14/REPORT_SHA256SUMS'
if ((Get-FileHash -LiteralPath $priorReport -Algorithm SHA256).Hash.ToLowerInvariant() -ne '94092dd51d3302515c132dcabbb4561344934db6ec916966c0bd9feb234008f1') { throw 'Prior outer report manifest changed' }
foreach ($line in Get-Content -LiteralPath $priorReport -Encoding UTF8) {
    $parts = $line -split '\s+', 2
    $actual = (Get-FileHash -LiteralPath (Join-Path (Split-Path $priorReport -Parent) $parts[1]) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $parts[0]) { throw ('Prior report changed: ' + $parts[1]) }
}
$null = New-Item -ItemType Directory -Path $work
$start = [DateTimeOffset]::UtcNow.ToString('o')
$argv = @('-d','FusionRehearsal','-u','root','--','timeout','--kill-after=20s','28800s','python3','-B','/mnt/c/Users/Peter/Documents/CODING/fsn-efsn/docs/evidence/restart-ticket-encoder-w-9300000-2026-10-14/inputs/replay_image.py')
[ordered]@{ started=$start; argv=$argv; dispatcher_pid=$PID; input_manifest_sha256=$inputHash } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $work 'dispatch.json') -Encoding utf8
& wsl.exe @argv 1> (Join-Path $work 'stdout.txt') 2> (Join-Path $work 'stderr.txt')
$code = $LASTEXITCODE
[ordered]@{ started=$start; finished=[DateTimeOffset]::UtcNow.ToString('o'); argv=$argv; exit=$code } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $work 'host-run.json') -Encoding utf8
exit $code
