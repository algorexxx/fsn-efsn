$ErrorActionPreference = 'Stop'
$patterns = @('efsn-telemetry\.test', 'efsn-wsl-server', 'efsn-wire-server', 'dashboard-telemetry-tests')
foreach ($attempt in @('attempt-1', 'attempt-2', 'attempt-3')) {
    $record = Get-Content -LiteralPath (Join-Path $PSScriptRoot "$attempt/result.json") -Raw | ConvertFrom-Json
    $patterns += [regex]::Escape($record.scratch_directory)
}
$remaining = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('node.exe', 'postgres.exe', 'wsl.exe') -and $_.CommandLine -match ($patterns -join '|')
} | Select-Object ProcessId, Name, CommandLine)
[pscustomobject]@{ remaining_test_processes = $remaining; count = $remaining.Count } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-process-cleanup.json') -Encoding utf8
if ($remaining.Count -ne 0) {
    throw 'Telemetry test processes remain'
}
