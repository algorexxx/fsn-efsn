# Complete-head and enrollment evidence

See [the report](../../restart-dashboard-enrollment.md) and
[consolidated launch plan](../../restart-plan.md).

| Artifact | Result |
| --- | --- |
| `baseline/` | Six new contracts fail on preceding production source |
| `contracts-1/` | 173 contracts and 13 socket tests pass |
| `attempt-1/` | Boundary profile reaches storage; wrong test expectation for disconnected freshness fails |
| `attempt-2/` | Corrected expectation; eight maximum-size inactive rows and rotated reconnect pass |
| `attempt-3/` | Eight concurrent reporters, two history batches and four advancing snapshots pass |
| `attempt-4/` | Actual synthetic efsn, direct RPC, PostgreSQL, HTTP API and four browser checkpoints pass |
| `attempt-5/` | Final boundary profile includes Primus Unicode escaping; eight inactive rows and rotated reconnect pass |
| `commit.json`, `dashboard-enrollment.patch` | Exact local dashboard revision, patch and runtime hashes |
| `verify.py`, `verification.json` | Source/build binding, result assertions and preservation checks |
| `check-*-processes.*`, `*-process-cleanup.json` | Windows/WSL cleanup evidence |

Each database attempt initializes a new SCRAM-authenticated loopback-only cluster,
stops it and removes its password file. Data remains under ignored `tmp/`.
`run.py` runs `enrollment`, `aligned` or the existing profile modes;
`run-actual.py` runs `actual-efsn` with the existing public-test-key node fixture
and unchanged compiled frontend. These are not production-database commands.

The boundary profile fills the head budget with synthetic uncle extra data;
it tests dashboard byte admission, not the consensus validity of those headers.
All test identities and credentials are synthetic. No real signing key, preserved
chain database, public network, deployment or dependency installation is involved.

Contract results predate the added opt-in enrollment integration file; their
production source and executed contracts match the final candidate. The final
profile strengthens only its metadata fixture with Unicode escaping; earlier
runs used the ASCII variant. The head fixture is identical. Earlier
failed integration output and its original source hashes remain intact. The
verifier explicitly distinguishes the corrected test expectation from production
changes and confirms the original dashboard checkout was preserved.
