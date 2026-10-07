# Release findings and dispositions

Updated 7 October 2026. This is the decision ledger for the
[selected candidate](restart-release-selection.md), under the existing
[R1–R10 acceptance matrix](restart-release-matrix.md). It replaces the matrix's
unclassified findings list. A disposition describes what to do; it is not a
claim that the finding has been independently approved or closed.

Technical preparation is handled in this investigation. Peter is the release
decision owner. Independent consensus and code-review assignees are not yet
named; their approval must be recorded before the applicable hold is cleared.
No human review or acceptance is inferred from a test pass.

| ID / affected rows | Finding and consequence | Disposition | Status / evidence needed to close |
| --- | --- | --- | --- |
| F1 — R1/R2/R3/R4 | Legacy `miner`, `core`, `core/rawdb`, broad `eth`, console and JS-tracer tests have obsolete APIs or removed symbols and cannot all compile. State tests now compile but expose inherited runtime failures tracked under F11. RPC `TestServer` lacks its testdata directory. Missing coverage can conceal regressions. | Treat as test-porting/coverage work. Keep focused passing tests and original failure logs. Two core/types fixture repairs now pass the complete package on D1 and the text experiment; production code is unchanged. Do not modify runtime APIs just to satisfy obsolete Ethereum tests or claim `go test ./...` passes. | Open review hold: repair the remaining relevant tests or document exact exclusions and replacement assertions on the selected compiler. Independent reviewer must approve the resulting coverage. |
| F2 — R7 | `TestParseNode` expects old DNS/parser errors and old Go URL error strings. | Correct the test expectations to the intended parser contract and pinned Go version; preserve rejection cases. Do not revert P12 DNS support to satisfy old text. | Technically resolved: deterministic resolver failure, structured URL-error assertions and unchanged valid identities. Corrected focused tests and ordinary discovery package tests pass with race detection on Go 1.27.1. Independent test review remains required. |
| F3 — R7 | `TestForwardCompatibility` supplies signed Ethereum discovery packet types 1–4, while Fusion uses 40–43. The old vectors fail before payload forward-compatibility is exercised. | Keep Fusion's wire numbers. Port the test vectors to Fusion with independently retained payload/identity expectations. Existing successful peer discovery alone does not replace the trailing-field assertion. | Technically resolved by six re-signed Fusion vectors. Payload bytes, extra-field expectations and signer identity are preserved; focused and ordinary package tests pass with race detection. No runtime protocol change. Independent test review remains required. |
| F4 — R7/R8 | `TestProtocolHandshake` reports disconnect size `got 2, want 1`. | Confirmed fixture error: `DiscReason` is a `uint8`, so its typed slice encodes as a byte string. Use `[]interface{}{DiscQuitting}` to require the RLP list sent by `SendItems`. The literal expected wire payload is `c1 08`: one-byte list payload, reason 8. | Technically resolved by the separate one-line test patch. Original failure reproduced with isolated loopback; corrected handshake passes with race detection in 1.022 s. No transport change. Independent test review remains required. |
| F5 — R2/G1 | Native execution ignores outer and inner RLP decode errors; partial/zero fields affect function choice, fees and balances. Raw-transaction validation also classifies data without first checking its recipient. | Preserve historical behavior in this minimal candidate; select no new activation height. Pool rejection is not a block-validation fix. Any correction needs an explicitly reviewed future activation and pre-activation compatibility. | **Release hold:** independent review must record consequences for newly admitted blocks and either justify the unchanged behavior or require a separately specified correction. Historical occurrence is not a safety finding. |
| F6 — R2/R6/R8 | The fixed anchor protects the accepted prefix. Equal-weight forks may need intervention; heavier compatible descendants can replace later transactions. | Keep ordinary Fusion fork choice and the existing operator response. No ongoing-finality design is selected. | Scope decision settled by the agreed design; final operator guidance/rehearsal must retain this limit. See the response guide. |
| F7 — R4/R5/R6 | Nonce gaps, saved purchases and ordinary ticket retreat losses can stop buying or require additional funds. | Use the demonstrated saved-byte/nonce repair procedure and supervised detection. Retain original signed purchases. Do not promise automatic gap repair or a universal reserve. | Operational hold until real wallet funding/runway, repair authority and host handover are recorded. Synthetic funded repair already passes. |
| F8 — R3/R7/R9 | Sparse historical state, header-only reconstruction limits, storage durability and inbound-only discovery leave supported-path boundaries. | Support Linux restored LevelDB without freezer, full sync and enabled outbound dialing. Keep read-only preservation and verified restore. Do not infer power-loss safety from process exits. | Scope restriction selected; final storage/host, restart/restore, advertised TCP/UDP and DNS checks remain required. |
| F9 — R1 | Go 1.21.3 is outside the current support window. Go 1.27.1 cannot link the inherited optional memsize integration. | Select Go 1.27.1 for qualification and the isolated B1 profiler removal. Remove its unused dependency entries. Keep the baseline replay toolchain unchanged. | Technical correction passes node build, CLI probes and same-host clean-cache binary comparison. Independent patch review and final compiler regression acceptance remain open. |
| F10 — R1/all affected rows | D1 technically remediates the two JWT findings. The selected candidate retains x/text and an unreviewed WebSocket entry with a disputed fixed version. The text experiment removes its advisory but also changes the main Go language version and compatibility defaults. The bounded language/default review is complete; required regression and history evidence is not. Recovery has WebSocket symbol presence but no source call finding. Lower-level findings remain. Existing CI uses Go 1.19. | Follow the [dependency report](restart-release-dependencies.md). Keep D1 selected and the text experiment unselected pending the recorded coverage/historical acceptance. Prefer qualifying upstream over a private backport without a demonstrated blocker. Resolve the other corrections; replace old CI after inputs are accepted. | **Release hold:** independent D1 review, remaining dependency remediation/dispositions, module/package review, a pinned CI/build image and affected acceptance are required. Successful scans do not constitute complete security acceptance. |
| F11 - R2/R3/G1 | Restored state tests expose inherited deletion-journal rollback defects: missing flag restoration for accounts without balance entries and a nil ordinary balance after reverting a time-locked asset. Both selected D1 and the text experiment fail identically. | Preserve the minimal failing regressions and unchanged production behavior while completing the bounded impact review. The empty-entry direct-API case alone does not prove EVM reachability. The EVM observation is now a completed bounded check (see the 7 Oct follow-up note below); completing that observation does not close this finding. Any runtime correction needs historical compatibility and an explicit activation decision. | **Release hold:** complete the impact/disposition review and obtain independent consensus review. No runtime fix or waiver is selected. The bounded EVM observation is complete and provenanced; the release finding stays open. |
| F12 — R2/R3/G5 | Current `DefaultGenesisBlock().ToBlock(nil)` produces a hash different from the registered mainnet genesis on both the selected baseline and F11 candidate. The in-memory probe does not establish the cause, actual CLI initialization behavior or any defect in the backup's stored genesis. | Keep verified restore/full sync as the supported launch path; genesis resync remains excluded. Preserve the failing equality assertion separately from synthetic configuration tests. Review the mismatch and the supported path's empty/mispointed-datadir refusal and restored identity checks. No genesis rewrite is selected. | Open disposition review under the existing G5 launch-path check. Record exact supported-command evidence and independent acceptance of the scope restriction; do not infer a mainnet genesis pass from synthetic initialization tests. |

## Evidence and source checks

- F1: [original miner compilation](evidence/restart-integrity-2026-09-23/baseline-package-tests.txt),
  [rawdb failure and anchor coverage](restart-anchor-implementation.md),
  [core fixture compilation](restart-parent-isolation.md), and
  [broad eth limitations](restart-autobuy-rebroadcast.md).
- F2/F3 reproduce on Go 1.27.1; [test-only patch 07](evidence/restart-release-followup-2026-10-04/07-discovery-fixtures.patch)
  then passes the three focused cases in 1.041 s and the discovery package in
  22.725 s, both with race detection. Two opt-in live tests are explicitly
  skipped; no fresh live-network pass is claimed. The
  [follow-up evidence](evidence/restart-release-followup-2026-10-04) preserves
  original vectors, test inputs and unchanged production inventories.
- F4's first new run timed out because the private
  network namespace left loopback down. The original timeout is retained as a
  harness failure; enabling only loopback reproduced the expected size mismatch.
  The [one-line test patch](evidence/restart-release-selection-2026-10-04/06-handshake-fixture.patch)
  then passes with race detection. This is not a passing full networking suite.
- F2–F4: [retained original failures](evidence/restart-discovery-2026-09-25/package-baseline-failures.txt)
  and the [current compiler probes](evidence/restart-release-selection-2026-10-04).
  `p2p/rlpx.go`, its original handshake test, native execution/validation and
  the original module manifests were checked unchanged between upstream and
  the extracted investigation input. B1 only removes the unused module entries.
- F5: [historical native-call report](native-call-decode-errors.md), including
  observed transactions and fee outcomes. No additional public-peer test or
  consensus change is authorized by this disposition.
- F6–F8: [operator response](restart-monitoring-response.md),
  [funded repair](restart-funded-gap.md), [network profile](restart-network-profile.md),
  [snapshot restore](restart-snapshot-restore.md) and
  [operator kit](restart-operator-kit.md).
- F9/F10: [compiler and source selection](restart-release-selection.md), exact
  build manifests and retained initial failure. The official
  [Go support policy](https://go.dev/doc/devel/release) and
  [download metadata](https://go.dev/dl/?mode=json) were checked on 4 October.
  The [offline dependency audit](restart-release-dependencies.md) retains four
  scan streams and distinguishes symbol/call findings from module presence.
  The subsequent [D1 qualification](evidence/restart-release-jwt-2026-10-04)
  removes both JWT IDs without adding dependencies or changing other linked
  modules. It preserves initial missing-cache failures and actual test scope.
- F1/F10: the [text experiment](evidence/restart-release-text-2026-10-04)
  verifies the upstream fix and passing builds/console checks without selecting
  the update. Console/tracer compilation failures are identical before/after;
  the RPC missing-fixture failure reproduces on D1. Its runtime-default changes
  and unresolved language/history acceptance remain explicit in the report.
- F1/F10: the [7 October follow-up](evidence/restart-release-go-defaults-2026-10-07)
  reviews the diagnosed loops and all 22 changed runtime-default overrides.
  Common/RLP and the repaired complete core/types package pass with race
  detection before/after. Original state compilation failures are identical.
  Test-only patch 10 preserves the existing wire/hash expectations. No D2
  production selection, blanket legacy override or full historical pass follows.

- F1/F11: [state fixture qualification](evidence/restart-state-tests-2026-10-07)
  ports four obsolete fixtures and preserves an independent dump vector.
  The final active overlay has 15 top-level passes and three failures on each
  build. Seven relevant runtime files match upstream exactly. The incomplete
  EVM probe is archived separately and is not a passing regression.

- F11 bounded EVM observation — completed and consolidated (7 Oct 2026):
  [restart-state-rollback-findings.md](restart-state-rollback-findings.md),
  following [restart-state-rollback-followup-opus.md](restart-state-rollback-followup-opus.md).
  The fixture was corrected and refined; the precondition for F11-a is isolated
  as the **absence of an ordinary-balance entry** for the self-destructed asset
  (not system vs non-system), the time lock is independently observed as
  restored, and the stray nil ordinary entry (read panic) is the defect. Re-run
  with full provenance against both the D1 baseline and the text experiment
  (identical results) in
  [evidence/restart-state-rollback-followup-2026-10-07](evidence/restart-state-rollback-followup-2026-10-07).
  Completing this observation does **not** close F11. No runtime change,
  release-input change, consensus activation, or accepted-block/historical claim
  is made. The run used the default network namespace; private isolation and
  zero network activity were not independently established. Go dependency
  settings do not supply that isolation. The
  [evidence correction](evidence/restart-state-rollback-followup-2026-10-07/README.md)
  supersedes the network-use claim while preserving the original artifacts.
- F11 source-based disposition proposal (7 Oct 2026):
  [restart-state-rollback-disposition.md](restart-state-rollback-disposition.md)
  compares leaving the inherited behavior with a narrow correction gated by
  block height. It identifies recovery-reader configuration, approval checksums
  and startup conflict handling as required parts of any candidate. The sole
  inspected production deletion caller supplies the balance entry that avoids
  F11-b; retain the direct-API defect and its scoped disposition for review.
  This is a source review, with no new test run, runtime change, selected
  activation or release waiver. F11 stays open.
- F11 isolated candidate (7 Oct 2026):
  [candidate and evidence](evidence/restart-state-rollback-candidate-2026-10-07/README.md)
  implement the proposed rule and shared schedule resolution without changing
  the selected source trees. The configuration suite and both command builds
  pass; the failed initial JSON expectation and its correction are retained.
  Follow the [qualification specification](restart-state-rollback-qualification.md)
  for startup/recovery integration and later execution boundaries. No candidate
  state/EVM/commit/block or historical pass is claimed. F11 stays open and the
  candidate remains unselected with no activation height.

- F11 startup/recovery integration (7 Oct 2026):
  [bounded integration evidence](evidence/restart-state-rollback-integration-2026-10-07/README.md)
  passes five top-level tests and 33 subtests with race detection. Rejected
  configurations make no observed mutation attempts; the read-only reader and
  startup agree across database close/reopen. Approval checks match independent
  JSON/hash vectors and reject other schedules before opening a signer. This
  uses a registered synthetic genesis, not real-mainnet initialization. The
  actual CLI report/prepare path remains open, as do execution/history phases.
  The inactive missing-header rejection remains an explicit compatibility-review
  item. No runtime/source-selection change or production schedule is selected.
- F12 genesis comparison (7 Oct 2026): the same bundle retains the original
  failed integration prerequisite, an initial diagnostic JSON-formatting failure,
  and the executed [baseline](evidence/restart-state-rollback-integration-2026-10-07/genesis-comparison-v2/baseline.txt)
  / [candidate](evidence/restart-state-rollback-integration-2026-10-07/genesis-comparison-v2/candidate.txt)
  invariant failures with provenance. Both construct the same different hash
  and state root. This is demonstrated in the selected recovery source/toolchain,
  not established for all upstream versions or historical compilers. The
  [operator kit](restart-operator-kit.md) already requires a verified restore
  marker and prohibits initializing a missing restored chain; validate these
  boundaries in the final supported-path check.

The missing production anchor, release version, accepted history, public
endpoints and signing approvals remain explicit release inputs in the main
plan. They are not additional runtime defects or reasons to expand this ledger
with speculative features.
