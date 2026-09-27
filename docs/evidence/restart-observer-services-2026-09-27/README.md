# Actual-service observer evidence

See the [report](../../restart-observer-services.md) for scope and interpretation.
Baseline: `8da6ce7`. No non-test Go source changed for this follow-up.

`run.sh attempt-N` is invoked through `wsl -d FusionRehearsal -u root --
unshare --net -- bash <absolute-script-path> attempt-N`. It enables loopback,
builds the observer and integration-test binary offline as `rehearsal`, and
runs the test in that private namespace. Source hashes cover both observer
packages and the existing restart test helpers. The Linux test requires its
explicit observer/output settings and refuses a configured large-backup input.

| Attempt | Outcome |
| --- | --- |
| 1 | Stopped at baseline Git capture because root did not trust the Windows-owned checkout. Added command-scoped `safe.directory` for this known workspace; no global setting changed. No build or service ran. |
| 2 | Compilation rejected an unused import in the new test. Removed it; no service ran. |
| 3 | Synthetic branch preparation succeeded, then the evidence writer correctly refused to overwrite an existing temporary `lab.json`. Switched that explicit test-configuration update to the existing `os.WriteFile` pattern. No service ran. |
| 4 | Passed all eight external CLI observations and both service shutdowns with race detection in 13.93 seconds. |

Attempt 4 retains:

- `sources.sha256`, `binaries.sha256`, `toolchain.txt`, `baseline.txt`: build
  identities. Empty build logs mean no compiler output.
- `services-race.txt`, `exit.txt`: parent and both child service results.
- `services/genesis.json`, `prepared-truth.json`, four block RLP files:
  synthetic input and independent state expectations.
- Eight configs, observer reports, stderr files and before/after state files:
  IPC/HTTP divergence, convergence, queued gap, disabled expected producer,
  wrong identity, endpoint loss and retired endpoint.
- `services/result.json`: completion only after all checks and clean shutdown.
- Network and capacity snapshots: isolated loopback, no D: free-space change
  during the passing run. No backup/database copy or W: operation occurred.

The compact fixture uses devnet rules and only public test keys 1 and 2. Its
balances, identity and timing are synthetic. Config endpoints refer to temporary
paths/ports. They are not production deployment artifacts. The services expose
test-only controls to the harness; observer invocations remain on their existing
read allowlist. The harness separately performs the controlled synchronization
and one signed test transaction submission between observations.

`verify.py` verifies retained report/state consistency, passing logs and source
hashes and writes `checks.json`. Binary hashes describe the built artifacts in
the workspace's ignored `tmp/restart-observer-services` directory. Previous
attempt manifests intentionally refer to their earlier test source revisions.
