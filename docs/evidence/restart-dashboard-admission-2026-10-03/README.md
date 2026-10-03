# Dashboard admission evidence

3 October 2026. See [the report](../../restart-dashboard-admission.md) for scope
and [the consolidated plan](../../restart-plan.md) for remaining launch gates.
All credentials/chain data in these tests are synthetic. No public service,
preserved chain database or real signing key was used.

| Evidence | Interpretation |
| --- | --- |
| `baseline/` | Node sandbox `EPERM` before tests loaded; not a valid regression run |
| `baseline-2/` | Previous production source: six tests, one pass and five expected failures |
| `contracts-1/` | Candidate: 167 contracts and 13 socket tests pass |
| `attempt-1/` | Actual node/browser reached checkpoints; zero-error assertion failed; transport cause not captured |
| `attempt-2/` | Same failure with diagnostics: two initial refused connections, later normal connection, cleanup close |
| `attempt-3/` | Bounded Windows-side readiness added; actual node/database/API/browser pass with zero writer errors |
| `dashboard-admission.patch`, `commit.json` | Exact local dashboard commit and parent, patch and runtime hashes |
| `verify.py`, `verification.json` | Assertions binding tests, runtime, source/build hashes, preserved original checkout and process cleanup |
| `check-*-processes.*`, `*-process-cleanup.json` | Windows and WSL cleanup checks |

`run-contracts.py` executes the listed root/wire scripts or the six new baseline
contracts. Its baseline exit-code flag alone does not distinguish an expected
assertion failure from an environment failure; `verify.py` checks TAP test counts
and the actual failures before accepting baseline-2 as evidence.

`run.py` creates a fresh SCRAM-authenticated loopback PostgreSQL cluster, uses the
existing public-test-key efsn binary and unchanged compiled browser, then stops
the cluster and removes its password. Each run records its runner, source/build
hashes and process outcomes. Scratch data remains under ignored `tmp/`.

The candidate and baseline share test fixture improvements; baseline production
files are explicitly checked against the parent commit. Later integration edits
only affect the opt-in actual-node fixture and are bound to attempt-3. Earlier
failures remain unchanged. No new production consensus, API, storage, dependency
or frontend behavior is introduced by the fixture readiness correction.

Run the verifier from the node repository with Python. Integration replay needs
the recorded Windows/WSL tooling and fresh disposable database configuration;
it is not a command for a public or preserved production database.
