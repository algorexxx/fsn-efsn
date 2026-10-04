# Release findings and dispositions

4 October 2026. This is the decision ledger for the
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
| F1 — R2/R3/R4 | Legacy `miner`, `core`, `core/rawdb` and broad `eth` tests have obsolete APIs or removed symbols and cannot all compile. Missing coverage can conceal regressions. | Treat as test-porting/coverage work. Keep focused passing tests and original failure logs. Do not modify runtime APIs just to satisfy obsolete Ethereum tests or claim `go test ./...` passes. | Open review hold: repair the relevant tests or document exact exclusions and replacement assertions on the selected compiler. Independent reviewer must approve the resulting coverage. |
| F2 — R7 | `TestParseNode` expects old DNS/parser errors and old Go URL error strings. | Correct the test expectations to the intended parser contract and pinned Go version; preserve rejection cases. Do not revert P12 DNS support to satisfy old text. | Test repair pending; verify invalid input still rejects and valid literal/DNS bootstrap paths retain their existing tests. |
| F3 — R7 | `TestForwardCompatibility` supplies signed Ethereum discovery packet types 1–4, while Fusion uses 40–43. The old vectors fail before payload forward-compatibility is exercised. | Keep Fusion's wire numbers. Port the test vectors to Fusion with independently retained payload/identity expectations. Existing successful peer discovery alone does not replace the trailing-field assertion. | Test repair pending; require valid signed Fusion vectors with preserved extra-field expectations. No runtime protocol change selected. |
| F4 — R7/R8 | `TestProtocolHandshake` reports disconnect size `got 2, want 1`. | Confirmed fixture error: `DiscReason` is a `uint8`, so its typed slice encodes as a byte string. Use `[]interface{}{DiscQuitting}` to require the RLP list sent by `SendItems`. The literal expected wire payload is `c1 08`: one-byte list payload, reason 8. | Technically resolved by the separate one-line test patch. Original failure reproduced with isolated loopback; corrected handshake passes with race detection in 1.022 s. No transport change. Independent test review remains required. |
| F5 — R2/G1 | Native execution ignores outer and inner RLP decode errors; partial/zero fields affect function choice, fees and balances. Raw-transaction validation also classifies data without first checking its recipient. | Preserve historical behavior in this minimal candidate; select no new activation height. Pool rejection is not a block-validation fix. Any correction needs an explicitly reviewed future activation and pre-activation compatibility. | **Release hold:** independent review must record consequences for newly admitted blocks and either justify the unchanged behavior or require a separately specified correction. Historical occurrence is not a safety finding. |
| F6 — R2/R6/R8 | The fixed anchor protects the accepted prefix. Equal-weight forks may need intervention; heavier compatible descendants can replace later transactions. | Keep ordinary Fusion fork choice and the existing operator response. No ongoing-finality design is selected. | Scope decision settled by the agreed design; final operator guidance/rehearsal must retain this limit. See the response guide. |
| F7 — R4/R5/R6 | Nonce gaps, saved purchases and ordinary ticket retreat losses can stop buying or require additional funds. | Use the demonstrated saved-byte/nonce repair procedure and supervised detection. Retain original signed purchases. Do not promise automatic gap repair or a universal reserve. | Operational hold until real wallet funding/runway, repair authority and host handover are recorded. Synthetic funded repair already passes. |
| F8 — R3/R7/R9 | Sparse historical state, header-only reconstruction limits, storage durability and inbound-only discovery leave supported-path boundaries. | Support Linux restored LevelDB without freezer, full sync and enabled outbound dialing. Keep read-only preservation and verified restore. Do not infer power-loss safety from process exits. | Scope restriction selected; final storage/host, restart/restore, advertised TCP/UDP and DNS checks remain required. |
| F9 — R1 | Go 1.21.3 is outside the current support window. Go 1.27.1 cannot link the inherited optional memsize integration. | Select Go 1.27.1 for qualification and the isolated B1 profiler removal. Remove its unused dependency entries. Keep the baseline replay toolchain unchanged. | Technical correction passes node build, CLI probes and same-host clean-cache binary comparison. Independent patch review and final compiler regression acceptance remain open. |
| F10 — R1/all affected rows | A successful build does not establish dependency security or final CI reproducibility. Existing CI uses Go 1.19; full module metadata is absent from the offline cache. | Keep the pinned existing dependency graph except removal of memsize for this candidate. Record actual linked modules. Perform dependency/advisory review before approving the release; make only justified, separately tested upgrades. Replace the old CI configuration after the qualification inputs are accepted. | **Release hold:** reviewed dependency findings, complete pinned CI/build image and affected acceptance are required. Neither the offline metadata failure nor a compiler update closes this item. |

## Evidence and source checks

- F1: [original miner compilation](evidence/restart-integrity-2026-09-23/baseline-package-tests.txt),
  [rawdb failure and anchor coverage](restart-anchor-implementation.md),
  [core fixture compilation](restart-parent-isolation.md), and
  [broad eth limitations](restart-autobuy-rebroadcast.md).
- F2/F3 reproduce on Go 1.27.1. F4's first new run timed out because the private
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

The missing production anchor, release version, accepted history, public
endpoints and signing approvals remain explicit release inputs in the main
plan. They are not additional runtime defects or reasons to expand this ledger
with speculative features.
