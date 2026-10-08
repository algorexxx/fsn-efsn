# Candidate historical replay through 300,000

8 October 2026. **Passed within the declared range.** The exact encoder-candidate
replay executable resumed from a verified copy of the 100,000 checkpoint and
imported blocks 100,001 through 300,000. The saved executable/source/config
identity was accepted unchanged. Both final cold checks passed against the
preserved source reference captured before replay.

All seven recorded commands exited zero, with no stderr, failed/skipped tests,
monitor retries or stop requests. Replay ran from 16:21:24 to 16:33:28 UTC
(about 12 minutes); final preservation checks finished at 16:33:40. The
[specification](spec.md) and [plan at start](plan-at-start.md) preceded execution.
[Verification](verification.json) checks commands, identities, observations,
source inventories, the one-line observer change and preservation evidence.

## Historical result

| Endpoint at 300,000 | Observed and matched |
| --- | --- |
| Block hash | `0x6e56fdb9825911fcf792fa299a4e2a1e143b7893cae712662bc22edfbcf7ab98` |
| State root | `0x277afc10704cb38db3525eacdabfbed9ba9a1d015fc50f0a6be9ca9ff65d13d7` |
| Ticket commitment | `0xbe62e940c6465fd6aa96e4468a250ffd1e784483eb5c691b996a2a20d84b5279` |
| Receipt root | `0xa97dd2e57c53518c38fd6dff8afd667453629eb56b5e1b2a2a147e4984cdec7a` |
| Cumulative difficulty | `860903030` |
| Transactions / receipts | `2 / 2` |

Full endpoint header RLP, transaction root and bloom also match the pre-replay
source observation. The separate cold-details process began with an empty
ticket cache, decoded state tickets and recomputed the preserved commitment.
Its **2,999 tickets** agree with the replay's final observation; this count was
observed, not assumed from the backup's unavailable historical state.

The original exact-height cold helper additionally checked all head markers,
canonical identity, body/receipt commitments and TD against the preserved
history. The replay and both cold checks ran in separate processes. This
extends the candidate's sequential execution evidence from genesis through
300,000, linking to the [first range](../restart-ticket-encoder-replay-100000-2026-10-08/README.md).
All these heights retain legacy checkpoint shortcuts through 2,680,000:
transaction execution and state/receipt comparisons run, while ticket-seal and
raw-transaction checks remain subject to those documented shortcuts.

## What changed for this run

The replay executable was copied byte-for-byte, not rebuilt. The new endpoint
observer was compiled separately on Go 1.27.1 using an overlay that changes
only the earlier details fixture's height literal from 100000 to 300000.
The [one-line diff](observer-change.patch), overlay, compiler identity and
observer hash are retained. Only its read-only reference/details tests ran;
its replay test was never invoked. Runtime source and compiler settings remain
identical to the first candidate range.

The [runner](run.py) imports the sealed first-range runner's existing execution,
environment, monitoring and preservation helpers. It pins and rechecks that
runner's hash. No prior evidence file was changed for reuse.

## Preservation and storage

- Backup and checkpoint had enforced read-only mounts inside private mount and
  network namespaces, with loopback down and Go downloads disabled.
- All **85 checkpoint files** matched the previous hashes before copying;
  copied bytes matched, and the original checkpoint still matches after work.
  The checkpoint cold preflight passed at exactly 100,000.
- All **161 stopped-target files** retained their SHA256 during final inspection.
  The replay identity file is byte-identical to the original checkpoint's.
- Backup metadata for 56,107 files and both baseline replay metadata inventories
  are unchanged. Neither baseline database was opened. This does not claim a
  new full-content hash of the 117 GB backup.
- Selected source, prior candidate source, copied source, both replay-binary
  copies, observer and overlay pass their preservation checks. All **991 prior
  manifested files** were rechecked.
- Closed target allocation: **456,945,664 bytes (435.78 MiB)**. Final free space:
  **43.10 GiB Linux / 89.48 GiB D:**. No W: storage or large backup copy was used.

## Retained inputs and remaining work

Target: `/home/rehearsal/replay/candidate-ticket-encoding-300000`.
Replay executable:
`/home/rehearsal/results/restart-ticket-encoder-replay-300000-2026-10-08/bin/replay-tests`.
SHA256: `b673229c4383efe2bdcdb8fae85606343f0823a3603b3f6a51c7e82e6d98f245`.
The original executable remains retained in the first-range result directory.
Keep this exact binary for future validated resume. The separate observer is
specific to 300,000; it must not replace the identity-bound replay executable.

Next is a bounded continuation through 600,000, preserving this checkpoint,
with fresh capacity checks and the same stop limits. It has not started.
F12 stays open for further history, independent codec/consensus/maintenance
review and restored-identity startup refusal. F11 and other findings are
unaffected. No production selection, activation, keys, public peers or mining
were changed.
