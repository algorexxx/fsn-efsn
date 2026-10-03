$taskProcesses = @(Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'efsn-telemetry\.test\.cjs|efsn-wsl-server\.cjs|wire-server\.cjs') -or
    ($_.Name -eq 'msedge.exe' -and $_.CommandLine -match 'playwright_chromiumdev_profile')
} | Select-Object ProcessId,Name,CommandLine)
$taskResult = @{remaining_test_processes = @($taskProcesses); count = $taskProcesses.Count}
$taskJson = $taskResult | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'windows-process-cleanup.json'), $taskJson, [System.Text.UTF8Encoding]::new($false))
$taskJson
if ($taskProcesses.Count -ne 0) { exit 1 }
