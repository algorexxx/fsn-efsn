# Candidate historical replay through 100,000

8 October 2026. **Passed within the declared range.** Frozen D1 node plus the
unselected legacy-compatible ticket encoder, compiled with Go 1.27.1, generated
the preserved genesis and imported blocks 1 through 100,000 into a new database.
All eight recorded commands passed. There were no failed/skipped tests, stderr
output, monitor retries or stop requests. The [verification](verification.json)
checks the retained logs, identities, source inputs and preservation records.

Replay ran from 16:01:14 to 16:07:32 UTC; final checks completed at 16:07:45.
The existing replay test reports 368.41 seconds, excluding process startup.
The [original scope](plan-at-start.md), [execution specification](spec.md),
[launcher](launch.py) and [runner](run.py) preceded execution.

## Historical agreement

The source endpoint was captured **before** candidate replay. After clean
shutdown, two fresh processes inspected the target on a read-only mount.
The original exact-height helper verified canonical/header/full/fast heads,
body transaction root, receipt count/root/bloom and cumulative difficulty
against the preserved source. The separate details check began with an empty
ticket cache, opened the resulting state, decoded its tickets and successfully
recomputed their commitment with the candidate encoder.

| Endpoint at 100,000 | Observed and matched |
| --- | --- |
| Block hash | `0x0e4a4045c06984472f86bb8f1e40bb70dee87b6227877ffcaeab7624db745cd2` |
| State root | `0x95697b558879524bead323328c9e97adce259ac7047a2140107704bf930d4741` |
| Ticket commitment | `0x1860459771b267e3b319ed899deb55a4ab973562f0d923309263244e1630020d` |
| Receipt root | `0x4d424b4cbfe8af1a48ed3491bd778b5be14a4af69f1896fff2dd03bef8a9f326` |
| Cumulative difficulty | `248744116` |
| Transactions / receipts | `1 / 1` |

Full header RLP, transaction root and bloom also match the pre-replay source
observation exactly. The cold target contains **2,630 tickets**, agreeing with
the replay's final observation. This count was observed, not invented as an
expected value or recovered from unavailable historical state in the backup.

Sequential import executed transactions and compared state/receipt commitments
throughout the range. The entire range retains legacy checkpoint shortcuts
through 2,680,000: ticket-seal and raw-transaction checks are not fully exercised
here. This is actual historical execution, but it is not complete historical
or independent consensus qualification.

## Preservation and cost

- Private mount and network namespaces, loopback down, offline Go modules,
  read-only source mount and read-only LevelDB opens for source/inspection.
- All 56,107 backup files retain the same filename/size/mtime inventory as
  before this run and the earlier compression investigation. This is metadata
  preservation plus enforced read-only access, not a new 117 GB content hash.
- Both baseline replay directories at 3,300,000 and 3,600,000 retain their
  before/after metadata inventories; neither database was opened.
- All **85 target files** have identical SHA256 before and after cold checks.
  Selected runtime source and candidate/test inventories remain unchanged.
- Closed target allocation: **227,385,344 bytes (216.85 MiB)**. Largest sampled
  allocation was 314.65 MiB, below the 4 GiB stop. This is a sampled peak, not
  a measured absolute maximum. Final space: **43.57 GiB Linux / 91.09 GiB D:**.
- All **954 previously manifested files** were rechecked. Exact command
  arguments, toolchain/build metadata, input/runtime/helper hashes, process
  isolation, size measurements and compressed metadata inventories are in
  [qualification/run.json](qualification/run.json) and adjacent files.

## Retained continuation inputs

Target: `/home/rehearsal/replay/candidate-ticket-encoding-100000`.

Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-100000-2026-10-08/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
Its generated [identity](qualification/replay-identity.json) binds this binary,
source genesis/head and source/replay configurations. Retain that exact
executable for validated continuation; do not rebuild it and relax the identity
check. The added endpoint-details tests are specific to 100,000. Later ranges
can use the original environment-driven replay/cold-head helpers in the same
binary; any new detailed observer must be a separate binary.

The candidate remains unselected. Further bounded history, independent
codec/consensus/maintenance review and restored-identity startup refusal remain
open under F12; F11 and other release findings are unaffected. No public peers,
keys, signing, mining, production configuration or release inputs were changed.
