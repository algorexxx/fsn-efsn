$ErrorActionPreference = 'Stop'
$patterns = @('efsn-telemetry\.test', 'efsn-wsl-server', 'efsn-wire-server', 'dashboard-presentation-tests', 'playwright_chromiumdev_profile-', 'metadata-admission-wire\.test')
foreach ($index in 1..3) {
    $record = Get-Content -LiteralPath (Join-Path $PSScriptRoot "attempt-$index/result.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    $patterns += [regex]::Escape($record.scratch_directory)
    if (Test-Path -LiteralPath (Join-Path $record.scratch_directory 'password.txt')) {
        throw 'Disposable database password remains'
    }
    if (Test-Path -LiteralPath (Join-Path $record.scratch_directory 'data/postmaster.pid')) {
        throw 'Disposable database still has a server PID file'
    }
}
$remaining = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @('node.exe', 'postgres.exe', 'wsl.exe', 'msedge.exe') -and $_.CommandLine -match ($patterns -join '|')
} | Select-Object ProcessId, Name, CommandLine)
[pscustomobject]@{ remaining_test_processes = $remaining; count = $remaining.Count } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-process-cleanup.json') -Encoding utf8
if ($remaining.Count -ne 0) {
    throw 'Dashboard admission test processes remain'
}
