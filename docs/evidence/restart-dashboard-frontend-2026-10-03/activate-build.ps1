$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$taskOld = Join-Path $taskRoot 'tmp/fsn-stats-auth/react-frontend/build'
$taskCandidate = Join-Path $taskRoot 'tmp/dashboard-frontend-build'
$taskRetained = Join-Path $taskRoot 'tmp/dashboard-frontend-build-before'
foreach ($taskPath in @($taskOld, $taskCandidate, $taskRetained)) {
    $taskAbsolute = [System.IO.Path]::GetFullPath($taskPath)
    if (-not $taskAbsolute.StartsWith($taskRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Build path is outside the workspace'
    }
}
if (Test-Path -LiteralPath $taskRetained) {
    throw 'The retained build path already exists'
}
$taskBaseline = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$taskBuild = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'frontend-1/result.json') -Encoding UTF8 -Raw | ConvertFrom-Json
function Confirm-BuildHashes($taskDirectory, $taskHashes) {
    $taskFiles = @(Get-ChildItem -LiteralPath $taskDirectory -Recurse -File)
    if ($taskFiles.Count -ne @($taskHashes.PSObject.Properties).Count) {
        throw 'Unexpected build file count'
    }
    foreach ($taskEntry in $taskHashes.PSObject.Properties) {
        $taskFile = Join-Path $taskDirectory $taskEntry.Name
        if ((Get-FileHash -LiteralPath $taskFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.Value) {
            throw ('Build hash differs: ' + $taskEntry.Name)
        }
    }
}
Confirm-BuildHashes $taskOld $taskBaseline.build_sha256
Confirm-BuildHashes $taskCandidate $taskBuild.build_sha256
Move-Item -LiteralPath $taskOld -Destination $taskRetained
Move-Item -LiteralPath $taskCandidate -Destination $taskOld
Confirm-BuildHashes $taskOld $taskBuild.build_sha256
Confirm-BuildHashes $taskRetained $taskBaseline.build_sha256
$taskResult = @{ activeBuild = $taskOld; retainedBuild = $taskRetained; hashesVerified = $true; oldBuildPreserved = $true }
$taskJson = $taskResult | ConvertTo-Json
[System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'build-activation.json'), $taskJson, [System.Text.UTF8Encoding]::new($false))
$taskJson
