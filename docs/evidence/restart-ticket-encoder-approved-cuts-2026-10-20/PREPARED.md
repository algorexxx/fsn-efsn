# Candidate approved-signing interruption and refusal acceptance

Prepared 20 October 2026 after verified complete-state operator completion,
committed as `c53d3473`. That run establishes the success path and exact legacy
artifact agreement. This run covers the remaining approved-signing process cuts
and refusal boundary under the unselected encoder candidate and Go 1.27.1.
Earlier candidate regressions exercised lower-level guard/journal behavior;
earlier approved interruption evidence used the legacy encoder/toolchain.

Run only these existing tests, once, race-enabled:

- `TestApprovedOfflineProcessCuts`: completion, export and import cuts at all
  three stages; reservation/signature cuts must leave an uncertain attempt that
  refuses signing and export before further signer access.
- `TestApprovedOfflineRefusals`: eight changed approvals; unreviewed digest,
  legacy journal/wrapper bypass, executable and configuration identity refusals.
- `TestKeystorePreflightLocksAndUncertain`: chain/journal locks held through
  password validation, wrong-password retry and refusal before credential access
  after an ambiguous signature.

The existing helpers use public scalars 1 and 2 and small synthetic databases
(each copied key/value batch is capped at 4 MiB). Test expectations and assertions
are unchanged. The sole behavioral harness adaptation replaces `t.TempDir()` in
`prepareOfflineRecovery` with a retained `MkdirTemp` allocation under this job's
fixture root. Seven fixture cases, including uncertain and failed cases, remain
on disk; there is no automatic fixture deletion. `harness-provenance.json`
records complete-file/exact-declaration sources and that adaptation. Additional
helpers compile to satisfy the established fixture dependency closure but are
not selected for execution.

Runtime code is the exact 1,225-file retained candidate-recovery selection from
the 8 October regression record, with only its test harness replaced. No runtime
implementation or release selection changes. The original retained tree is
bound read-only in a private mount namespace. All new source, binaries, caches
and fixtures stay under the matching C: `tmp/` directory. No backup database,
compact export, replay checkpoint or image is opened.

The launcher reuses the existing private network/mount namespace and one-owner
pattern. Only loopback exists, down. It refuses other test/node/build processes
and any loop device except an unrelated read-only autoclear Docker ISO. The
investigation lock is held throughout. Original backup, local fallback and
independent recovery metadata are compared before/after; Windows compares both
detached W: image lengths/timestamps.

Capacity/finite limits:

- Host admission: at least 2 GiB available RAM and 50 GiB free on C: and D:.
- Running reserves: Linux 20 GiB, D: 50 GiB, C: 40 GiB.
- Sampled logical job ceiling: 4 GiB; samples every 30 seconds during commands.
- One compiler worker, one Go scheduler, 512 MiB Go memory target, low priority.
- Offline module fetch, local pinned Go 1.27.1, linux/amd64/v1, CGO, race build.
- Build 900 seconds; test 900 seconds internally, 960 externally.
- Worker cooperative 2,100 seconds, external 2,220; host 2,400 seconds.
  External limits use a 20-second termination grace.

Preflight verifies the preceding operator's 109-file seal
`9e0fc4b36679a5dae9779c3d021ade2d2c3ee6cff0caf5ab1043bb3b9f60052a`
and the 139-file candidate regression seal
`59bea0c464a9a089518e3454c646b381369691f3f4e00ee774730a4c8c2b400c`.
The compiler SHA-256 remains
`30969f97169d7f43fe6a085873d75613adc21e30818a8c61d95bd27275df4624`.
Exact build-source and executable inventories are recorded and rechecked.

Acceptance requires all three top-level tests, five cut subtests, eight refusal
subtests, nine exact-recovery/cold-ledger observations, both uncertain refusals
and credential-lock behavior, without skips or race reports. Every test child
must exit before closed-fixture hashes are taken. Preserve logs and artifacts,
verify resource/identity/cleanup records and commit results before other work.
No automatic retry or duplicate writer is permitted.

This does not qualify real-key custody, copied-journal rollback, storage
power-loss durability, selected release packaging or human approval. After this
test, reassess whether remaining work requires independent codec/consensus,
accepted-parent/trust, release selection and real-artifact decisions. Do not
invent more unchanged test runs to fill those review gaps.
