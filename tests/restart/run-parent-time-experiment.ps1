param([string]$Go = 'go')

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$overlayRoot = Join-Path $repositoryRoot 'tmp\restart-reconstruction-overlay'
$utf8 = New-Object System.Text.UTF8Encoding($false)
New-Item -ItemType Directory -Path $overlayRoot -Force | Out-Null

$sourcePath = Join-Path $repositoryRoot 'consensus\datong\consensus.go'
$testPath = Join-Path $repositoryRoot 'tests\restart\reconstruction_test.go'
$source = [IO.File]::ReadAllText($sourcePath, $utf8)
$test = [IO.File]::ReadAllText($testPath, $utf8)
$before = 'tickets, err = tickets.ClearExpiredTickets(header.Time)'
$after = @'
cleanupParent, err := getParent(chain, header, nil)
	if err != nil {
		return nil, err
	}
	tickets, err = tickets.ClearExpiredTickets(cleanupParent.Time)
'@
$testBefore = 'const expectParentTimeReconstruction = false'
$testAfter = 'const expectParentTimeReconstruction = true'
if (($source.Split(@($before), [StringSplitOptions]::None)).Count -ne 2) {
    throw 'Expected exactly one reconstruction cleanup expression; review the experiment against the new source.'
}
if (($test.Split(@($testBefore), [StringSplitOptions]::None)).Count -ne 2) {
    throw 'Expected exactly one reconstruction expectation switch; review the experiment against the new tests.'
}
$sourceCopy = Join-Path $overlayRoot 'consensus.go'
$testCopy = Join-Path $overlayRoot 'reconstruction_test.go'
[IO.File]::WriteAllText($sourceCopy, $source.Replace($before, $after), $utf8)
[IO.File]::WriteAllText($testCopy, $test.Replace($testBefore, $testAfter), $utf8)
$replacements = @{}
$replacements[$sourcePath] = $sourceCopy
$replacements[$testPath] = $testCopy
$overlayPath = Join-Path $overlayRoot 'overlay.json'
[IO.File]::WriteAllText($overlayPath, (@{ Replace = $replacements } | ConvertTo-Json -Depth 4), $utf8)

Push-Location $repositoryRoot
try {
    & $Go test -overlay $overlayPath ./tests/restart -v -count=1 -timeout=90s
    $testExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $testExitCode
