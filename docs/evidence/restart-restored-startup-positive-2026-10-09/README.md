# Restored startup candidate — positive follow-up, 9 October 2026

**PASS for four actual CLI phases in an isolated synthetic archive-mode fixture.**
Reuse the [first run's fifteen verified refusals](../restart-restored-startup-candidate-2026-10-09/README.md)
and preserve its positive-path shutdown failure. No passing refusal was rerun.
The [verification result](verification.json) and [run record](qualification/run.json)
retain the checks and their limits.

| Phase | Result |
| --- | --- |
| Restore below the configured anchor | Starts for catch-up at the synthetic parent; no mining/auto-buy |
| Restore at the configured anchor | Starts at the expected parent; no mining/auto-buy |
| Import through local console `admin.importChain` | Returns true and advances to the independently tested child |
| Fresh-process restart | Loads that child with the same original anchor; no mining/auto-buy |

All processes exit zero and report clean blockchain shutdown. Preflight's
read-only open precedes writable protocol initialization in each log. The test
registers a synthetic genesis/anchor in the CLI process; that test profile is
excluded from the runtime patch. Heights 15,130,080/15,130,081 refer to the
synthetic fixture and do **not** extend G1 historical assurance.

The same retained seeder and CLI executables were used without rebuilding:

- CLI SHA256 `07aa74a3f58132e5ff1465152402d5ea3b01738c0017af5dfd5672a75a2550cd`.
- Seeder SHA256 `3a27b2af6bcaf425efb0ab116343b550f80148cc37b29af2d9b543a7ce72cff8`.
- The first run's complete build-source inventory and encoder-candidate node
  inventory match before and after. The fifteen refused databases still match
  their recorded cold hashes. The failed run's entire case inventory is preserved.
- Only a fresh small fixture advances; the original backup, replay database,
  recovery checkpoint and sealed historical evidence are not opened or copied.

The corrected fixture explicitly uses `--gcmode archive`, matching its seed's
`TrieDirtyDisabled` configuration. It still lacks earlier history, and its bloom
indexer reports missing canonical block 1. These logs are retained. This is
startup/import/restart evidence for that declared fixture, not full-history
indexing, explorer operation, pruning-mode shutdown or public-release acceptance.
The original panic is not suppressed, relabelled or fixed by a runtime change.

The seeder uses public test key 1 only. The CLI has no validator account and
performs no mining or auto-buy. It uses a separate network namespace with only
loopback down, explicit no-dial/discovery flags and empty peer lists. No public
network contact occurs. Each CLI has a 45-second external limit; the seeder has
60-second Go / 90-second external limits, all with ten-second kill grace. One
Go worker and niceness 10 limit contention with replay. Runtime/source identities,
command arguments, timestamps and before/after disk capacity are recorded.

## Candidate scope and remaining acceptance

The [three-file candidate patch](../restart-restored-startup-candidate-2026-10-09/qualification/candidate.patch)
contains two helpers and a three-line call before `eth.New` opens writable chain
data. It is unselected and stored only as evidence. It uses the existing restart
anchor as the trigger, validates the expected genesis and all persisted config
fields, reuses anchor/head validation, rejects a genesis-only full head, and
reads the full-head state and ticket commitment before allowing startup. Normal
compatible descendant import remains under the existing consensus rules.

No new launch flag or production anchor is introduced. When no restart anchor
is configured, the normal existing startup behavior remains. The final release
must therefore contain its approved anchor and supported network profile; this
prototype is not a universal guard for arbitrary custom-genesis/unanchored use.
An authenticated restore package remains necessary. Root/ticket access is not a
complete account/storage/code integrity scan. Exact config comparison is deliberate
for this frozen candidate; later reviewed upgrades need their own compatibility
disposition. The preflight also repeats existing ancestry checks, so selected-host
startup cost must be considered before shipping.

Next useful checks are narrowly scoped: malformed/locked or unreadable LevelDB
refusal, a complete-history small fixture under the supported pruning setting,
and read-only application of the candidate checks to the preserved complete
snapshot when replay no longer competes for that source. Keep recovery-tool
plan/parent authentication and final selected-candidate handover acceptance
separate. Do not repeat unchanged package/anchor/recovery suites. Final release
selection, independent review, actual approved restore/anchor inputs and G1/F12
historical compatibility remain open.
