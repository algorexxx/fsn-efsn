# Complete snapshot evidence, 24 September 2026

Baseline commit: `0ad0136`. Packaging, original-file comparison, complete restore,
index comparison and both service processes passed. The pipeline completed at
2026-09-24 23:25:57 UTC (25 September 01:25:57 Stockholm). Interpretation and limitations belong in
[restart-snapshot-restore.md](../../restart-snapshot-restore.md).

## Files and scope

- `windows-package-tests-final.txt` and `linux-package-tests-final.txt`: thirteen
  Python packaging/restore cases, including
  bounded resume, changed input, corrupt archive, unsafe paths, interrupted
  output, orphan-archive adoption, storage reserve and completion-marker rules.
  The final additions check exclusion across real processes, same-size/time
  source-content mutation, and failed output readback withholding the marker.
  `windows-package-tests.txt` retains the earlier ten-case run.
- `windows-source-lock.txt`: read-only source open excludes a concurrent writer
  and leaves the sentinel data unchanged, using a disposable database.
- `check-active-lock.py` and `active-smb-lock.txt`: while the full packager was
  running, a separate process attempted its actual W: package lock and was
  refused. The probe must be run only while that writer is active.
- `pack-pilot.txt`: two real source-data archives, then a bounded stop without a
  final manifest. `pack-full.txt` records explicit resume from those two parts.
  The final run passes with 220 parts; `pack-exit-code.txt` records exit zero.
- `source-index-inventory.json` and `.txt`: read-only source inspection. The
  report states the sampling scope; zero transaction lookups were missing.
- `inspect-log-fixture.go.txt` and `source-log-fixture.txt`: a bounded read-only
  inspection confirms block 2,700,000 has four transactions and ten logs, so the
  indexed RPC query has a positive result to compare. The initial versions
  printed hash bytes through `%s`; the final probe explicitly uses `Hash.Hex()`.
  Both probes required the exact preserved head and genesis before reading.
- `inspect-signing-context.go.txt`, `source-signing-context.json` and `.txt`:
  read-only enumeration of all saved header hashes at heights 15,130,080 through
  15,130,083, including noncanonical records. Only the expected canonical head
  exists; its signature verifies. The three later heights contain no headers.
  Iterator errors are checked before release. This covers this database only,
  not signatures retained elsewhere or in another record format.
- `verify-source-manifest.py`: pins the earlier independently retained backup
  manifest, compares all packaged file hashes to it, then records the accepted
  manifest hash and exact final manifest bytes. It must run only after packaging
  completes. Its report is a prerequisite of `run-restore.ps1`.
  `source-manifest-match.json`, `verify-source-manifest.txt` and
  `package-manifest.json` now record a complete match for all 56,107 files.
- `run-restore.ps1`: verifies that reviewed hash, requires a new W: target and
  available capacity, restores every file, and retains the completion marker.
  `restore.txt`, `restore-exit-code.txt` and `restored.json` record the passing
  complete extraction and final readback of all 56,107 files.
- `check-restored.ps1`: checks restored indexes against the source report and
  runs the actual node through startup/RPC/loopback-peer/clean-stop in each of
  two separate processes, preventing reuse of in-memory caches across restarts.
  Both runs check the preserved backup/donation balances through native and
  Ethereum-compatible RPC, together with their canonical nonces.
  It opens only the restored instance for writing. There is no validator wallet
  or mining; public test scalars 3 and 4 are P2P identities only.
  `restored-index-inventory.json` is byte-identical to the source report.
  `restored-service.txt`, `restored-service-reopen.txt`,
  `restored-check-exit-code.txt` and `pipeline-status.json` record success.
- `build-windows.ps1`: builds the portable test harness from the current sources
  with the pinned offline Go 1.21.3 setup. Compilation failure output is retained
  below; a successful build can produce no output.
- `finish-rehearsal.ps1`: queues the manifest comparison, restore and service
  checks after the running package process records a successful exit and creates
  the final manifest. Failures stop the sequence and record the failed stage.

## Storage and reproduction

The original database is
`C:/Users/Peter/Documents/CODING/fusion-node/data/efsn/chaindata`. It remains the
read-only source. W: maps to `//192.168.1.250/mnemosyne1`; all new large output
lives under `W:/FusionRestart/restore-rehearsal-2026-09-24`.

Run the Go binary from `tests/restart`, with these explicit settings for the
source packaging test:

```powershell
$env:GOMAXPROCS = '2'
$env:FUSION_RESTART_FULL_AUDIT = '1'
$env:FUSION_RESTART_CHAINDATA = 'C:/Users/Peter/Documents/CODING/fusion-node/data/efsn/chaindata'
$env:FUSION_RESTART_PACKAGE = 'W:/FusionRestart/restore-rehearsal-2026-09-24/package'
$env:FUSION_RESTART_PACKAGE_MAX_PARTS = '2'
& ../../tmp/snapshot-restore-windows-tests.exe '-test.run=^TestPreservedSnapshotPackage$' '-test.v' '-test.timeout=4h'
```

The first invocation requires a new package directory. For continuation, unset
`FUSION_RESTART_PACKAGE_MAX_PARTS` and set `FUSION_RESTART_PACKAGE_RESUME=1`.
Do not rerun against changed source files or a modified Python helper; its exact
bytes are pinned by the source plan. Use `STOP-PACKAGE` at the rehearsal root
instead of killing its Go lock-holder. Run verification, restore and restored
checks sequentially after a complete package. Restore is not resumable; a failed
target remains unverified and must not be started.

The original-manifest comparison proves agreement with the earlier copy of this
same backup. It is not an independent node's endorsement of chain history.
Publishing a release requires authenticated provenance and a reviewed recovery
head/anchor beyond this preserved historical head.

## Retained setup failures and performance probe

`windows-service-build.txt` records initially missing cached transitive node
dependencies. `copy-cached-deps.sh` copied their pinned module downloads from the
existing WSL cache into the C: workspace cache; it did not fetch new versions.
`windows-service-build-final.txt` records a harness API mistake (`Accounts`
instead of this fork's `Wallets`). The corrected harness subsequently compiled.
Neither failure required a production client change.

Static review also removed a generic Ethereum assumption from the prepared peer
test before it ran: Fusion repurposes the header's uncle-hash slot as its PoS
sorting hash. Returned uncle content is compared to the preserved body instead.
The chain's existing header rule was not changed.

`forward-only-probe.py` and `.txt` retain a one-part buffered, forward-only ZIP
experiment: 536,746,526 bytes, 10.94 seconds writing and 16.92 seconds including
readback hashing. It ran alongside packaging and did not establish a speedup;
the package format was not changed. Its archive remains in the dedicated W:
rehearsal root and is not part of the final manifest. An earlier 16 MiB native
storage probe also remains there. Neither probe is a chain-data artifact.

The full original, replay checkpoints and compact state fixture are retained.
No real key was read, real block signed, public peer contacted or archive
published in this work.

Evidence bytes are excluded from Git newline normalization. `identities.json`
records source/toolchain/binary identities; `SHA256SUMS` covers all other files.
The baseline is explicitly pinned because offline-signing work was committed
while this unchanged restore harness continued running.
