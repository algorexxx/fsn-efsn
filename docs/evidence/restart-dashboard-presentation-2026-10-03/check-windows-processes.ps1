$ErrorActionPreference = 'Stop'
$patterns = @('efsn-telemetry\.test', 'efsn-wsl-server', 'efsn-wire-server', 'dashboard-presentation-tests', 'playwright_chromiumdev_profile-')
foreach ($attempt in @('attempt-2')) {
    $record = Get-Content -LiteralPath (Join-Path $PSScriptRoot "$attempt/result.json") -Raw | ConvertFrom-Json
    $patterns += [regex]::Escape($record.scratch_directory)
}
$remaining = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('node.exe', 'postgres.exe', 'wsl.exe', 'msedge.exe') -and $_.CommandLine -match ($patterns -join '|')
} | Select-Object ProcessId, Name, CommandLine)
[pscustomobject]@{ remaining_test_processes = $remaining; count = $remaining.Count } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-process-cleanup.json') -Encoding utf8
if ($remaining.Count -ne 0) {
    throw 'Telemetry test processes remain'
}
