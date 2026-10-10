$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$started = [DateTime]::UtcNow.ToString('o')
$worker = Join-Path $PSScriptRoot 'archive.ps1'
$tokens = $null
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($worker, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$function = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Read-StreamDigest' }, $true)
. ([ScriptBlock]::Create($function.Extent.Text))
function Save-Progress($phase, [long]$bytes, [long]$total, [bool]$force) { }
$timer = [Diagnostics.Stopwatch]::StartNew()
$deadlineSeconds = 60
$source = [IO.MemoryStream]::new([Text.Encoding]::ASCII.GetBytes('abc'))
$target = [IO.MemoryStream]::new()
try {
    $digest = Read-StreamDigest $source 'synthetic-copy' 3 $target
    if ($digest -cne 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad' -or [Text.Encoding]::ASCII.GetString($target.ToArray()) -cne 'abc') { throw 'Published SHA256 abc vector or copied bytes differ.' }
    $readback = Read-StreamDigest $target 'synthetic-readback' 3 $null
    if ($readback -cne $digest) { throw 'Readback differs.' }
    $lengthRefused = $false
    try { $null = Read-StreamDigest $source 'synthetic-length-mismatch' 4 $null } catch { $lengthRefused = $_.Exception.Message -eq 'Complete file length differs from the source inventory.' }
    if (-not $lengthRefused) { throw 'Length mismatch was not refused.' }
} finally { $source.Dispose(); $target.Dispose() }
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('fusion-archive-lock-' + [Guid]::NewGuid().ToString('N') + '.txt')
[IO.File]::WriteAllText($fixture, 'abc', [Text.UTF8Encoding]::new($false))
$lock = [IO.File]::Open($fixture, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
$denied = $false
try {
    try { $writer = [IO.File]::Open($fixture, [IO.FileMode]::Open, [IO.FileAccess]::Write, [IO.FileShare]::ReadWrite); $writer.Dispose() } catch [IO.IOException] { $denied = $true }
    if (-not $denied) { throw 'Source read lock did not refuse a writer.' }
} finally { $lock.Dispose() }
if ((Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad') { throw 'Lock fixture changed.' }
$result = [ordered]@{ Passed=$true; Started=$started; Finished=[DateTime]::UtcNow.ToString('o'); WorkerSHA256=(Get-FileHash -LiteralPath $worker).Hash.ToLowerInvariant(); Checks=@('PowerShell parser','published SHA256 abc and exact copy','independent readback','length mismatch refused','Windows read-lock refuses writer'); RetainedTemporaryFixture=$fixture }
$path = Join-Path $PSScriptRoot 'qualification.json'
if (Test-Path -LiteralPath $path) { throw 'Preserve previous qualification.' }
[IO.File]::WriteAllText($path, ($result | ConvertTo-Json -Depth 5) + "`n", [Text.UTF8Encoding]::new($false))
$result | ConvertTo-Json -Depth 5
