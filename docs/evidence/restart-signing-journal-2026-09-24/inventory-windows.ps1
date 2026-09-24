$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$node = 'C:/Users/Peter/Documents/CODING/fusion-node/data/efsn'
$database = Join-Path $node 'chaindata'
$utf8 = [Text.UTF8Encoding]::new($false)
$report = Join-Path $PSScriptRoot 'backup-purchase-inventory.json'
if (Test-Path -LiteralPath $report) { throw 'Report already exists' }
function Read-DatabaseInventory {
    @(Get-ChildItem -LiteralPath $database -Recurse -File | Sort-Object FullName | ForEach-Object {
        $hash = $null
        if ($_.Name -match '^(CURRENT(\..*)?|MANIFEST-.*|LOG(\..*)?|LOCK|[0-9]+\.log)$') {
            $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        [pscustomobject]@{ Path=$_.FullName; Length=$_.Length; LastWriteTicks=$_.LastWriteTimeUtc.Ticks; MutableSHA256=$hash }
    })
}
$before = Read-DatabaseInventory | ConvertTo-Json -Depth 4
$compressed = [IO.File]::Create((Join-Path $PSScriptRoot 'backup-file-inventory.json.gz'))
$gzip = [IO.Compression.GZipStream]::new($compressed, [IO.Compression.CompressionLevel]::Optimal)
try { $gzip.Write($utf8.GetBytes($before)) } finally { $gzip.Dispose(); $compressed.Dispose() }
$journalBefore = Get-FileHash -LiteralPath (Join-Path $node 'transactions.rlp') -Algorithm SHA256
$env:GOMAXPROCS = '2'
$env:FUSION_RESTART_PURCHASE_INVENTORY = $node
$env:FUSION_RESTART_PURCHASE_INVENTORY_OUTPUT = $report
Push-Location (Join-Path $workspace 'tests/restart')
try {
    & ../../tmp/recovery-signing-final-windows-tests.exe '-test.run=^TestBackupPurchaseInventory$' '-test.v' '-test.timeout=2m' 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'backup-inventory-run.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Backup inventory failed' }
} finally {
    Pop-Location
    Remove-Item Env:FUSION_RESTART_PURCHASE_INVENTORY
    Remove-Item Env:FUSION_RESTART_PURCHASE_INVENTORY_OUTPUT
}
$after = Read-DatabaseInventory | ConvertTo-Json -Depth 4
$journalAfter = Get-FileHash -LiteralPath (Join-Path $node 'transactions.rlp') -Algorithm SHA256
if ($before -ne $after -or $journalBefore.Hash -ne $journalAfter.Hash) { throw 'Backup files changed' }
$digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($utf8.GetBytes($before))).ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'backup-inventory-equality.json'), (@{ BeforeSHA256=$digest; AfterSHA256=$digest; Equal=$true } | ConvertTo-Json), $utf8)
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'backup-preservation.txt'), "PASS: All database file names, lengths and last-write ticks agree; mutable database files and transactions.rlp have unchanged SHA-256 hashes. Immutable SST/freezer contents were not rehashed. No key file contents were opened.`n", $utf8)
