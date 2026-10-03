# Bounded dashboard profile evidence

See [the investigation report](../../restart-dashboard-profile.md) for results,
limits and next work. All traffic is synthetic and loopback-only. Every attempt
uses a fresh PostgreSQL cluster; no efsn process or real key is involved.

| Artifact | Purpose |
| --- | --- |
| `attempt-1` | Preserved failed fixture: waited for `onError`, but the transport limit emitted only close |
| `attempt-2` | Two-node 64 KiB receiver refusal observed via close 1009; no save |
| `attempt-3` | Eight-node 256 KiB output refusal observed via close 1006; no save |
| `attempt-4` | Initial successful eight-node 4/1/1 MiB profile on previous writer |
| `baseline-observability` | Twelve snapshot-writer tests: ten pass, two new diagnostic regressions fail |
| `contracts-1` | Candidate: 161 contracts and 12 socket tests pass |
| `attempt-5`, `attempt-6` | Both refusal cases pass with exactly one new error callback |
| `attempt-7` | Candidate eight-node profile passes after diagnostic fix |
| `attempt-8` | Six existing collector/database/API scenarios pass, including deliberate connection loss |
| `attempt-9` | Final eight-node case also sends a second history batch while persistence is active |
| `dashboard-profile.patch`, `commit.json` | Exact local dashboard commit and patch identity |
| `verification.json` | Source/provenance, assertions, unchanged runtime/efsn/original-checkout checks |
| `windows-process-cleanup.json` | Final no-matching-process check across all scratch clusters |

Only `test/dashboard-profile.test.cjs` changed between the contract/database
runs and the final case: the successful branch adds the second history batch
and its expected count. Source manifests preserve each attempt. The production
writer and all other executable sources match the final commit in the candidate
runs. Historical attempts are never overwritten.

`run.py attempt-N small-snapshot|small-output|aligned|persistence` reproduces a
bounded scenario with explicit local prerequisites and a new attempt directory.
`run-contracts.py contracts-N candidate` captures the ordinary suites.
`verify.py` checks the frozen evidence and source identities. Each profile records
message sizes/events rather than retaining its large generated bodies. The test
compares complete transaction arrays at runtime; its generator is in the patch.

Sampling hooks observe memory during parsing/writing and on a 25 ms timer. They
add overhead and do not measure continuous peak memory or production capacity.
The expiry assertion uses an injected clock. The nine stopped cluster directories
remain under the ignored `tmp` directory; no password file is retained.
