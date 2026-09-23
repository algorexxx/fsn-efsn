$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$logRoot = Join-Path $repositoryRoot 'tmp\restart-wsl-install'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$isElevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (!$isElevated) { throw 'Windows requires an administrator process to install the WSL platform.' }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
Start-Transcript -LiteralPath (Join-Path $logRoot 'install.log') -Force | Out-Null
try {
    & "$env:SystemRoot\System32\wsl.exe" --install --no-distribution --web-download
    $installExitCode = $LASTEXITCODE
    $feature = Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
    $result = [ordered]@{
        recordedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
        installExitCode = $installExitCode
        virtualMachinePlatform = [string]$feature.State
        rebootRequestedByScript = $false
        distributionInstalledByScript = $false
    }
    [IO.File]::WriteAllText((Join-Path $logRoot 'result.json'), ($result | ConvertTo-Json), $utf8)
}
catch {
    [IO.File]::WriteAllText((Join-Path $logRoot 'error.txt'), $_.Exception.Message, $utf8)
    throw
}
finally {
    Stop-Transcript | Out-Null
}
