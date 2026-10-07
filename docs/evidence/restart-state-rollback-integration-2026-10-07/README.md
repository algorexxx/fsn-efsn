# F11 startup and offline recovery integration

7 October 2026. This continues phase 2 of the
[qualification specification](../../restart-state-rollback-qualification.md)
against the unselected [candidate](../restart-state-rollback-candidate-2026-10-07/README.md)
from `8357c5fe`. The selected P1–P17+B1+D1 source trees and candidate runtime
files were not changed. No production activation height is selected.

## Results and limits

The [second integration run](qualification-v2/tests.txt) passes five top-level
tests and 33 subtests with race detection on Go 1.27.1:

| Test | Observation |
| --- | --- |
| Startup configuration, 20 subtests | Legacy configuration before the boundary resolves the approved test schedule; missing/changed active schedules, wrong identity and missing header metadata are rejected. Rejections have no observed database mutation attempts and leave every key/value unchanged. Errors are not `ConfigCompatError`, including the zero-rewind boundary, so they do not request the backend's config rewind. Valid custom schedules retain their semantics. |
| Recovery reader, seven subtests | The reader resolves the same rule without writes, rejects missing/changed active schedules, and keeps custom-network configuration separate. |
| Database close/reopen | A read-only LevelDB reopen resolves the effective configuration without changing stored key/values. Startup persists the permitted schedule; another close/reopen retains the same configuration and stored key/values. |
| Fresh initialization, four subtests | The registered synthetic network initializes successfully. Conflicting schedule, wrong chain ID and negative custom schedule are rejected without partial database initialization. This is not a passing real-mainnet genesis check. |
| Approval binding, two subtests plus a positive context check | Effective configuration JSON and SHA-256 match independently generated Python vectors. A matching approval passes `checkApprovalContext`. Approvals for legacy/different schedules fail through `signApprovedOffline` before the signer callback opens; the chain key/values stay unchanged. |

The database wrapper delegates to real memory/LevelDB operations and counts
direct and queued batch mutations; it does not substitute database results.
The database close/reopen occurs within one test process. It is not a fresh
node-process boot, crash recovery or power-loss result. The fixture writes
synthetic head/index records, not a consensus-validated chain.

The signer is only a rejection-path callback with a call counter. No real keys
are loaded, no transaction or block is signed, and the positive check does not
run a complete signing flow. Actual CLI review-report construction and prepare
handling of the resolved configuration remain untested in this bundle.
Candidate rollback, finalization/commit, block processing and historical
compatibility remain later phases. F11 stays open.

The candidate's earlier header-number lookup also rejects a missing index
with the rule unselected. This behavior is observed, not a claim of complete
inactive-path compatibility; its scope remains part of candidate review.

## Synthetic network identity and separate genesis finding

The original integration fixture assumed current default genesis construction
reproduced the registered mainnet hash. It failed that prerequisite. The
separate [probe](genesis_probe_test.go) retains the equality assertion and
fails on both the selected baseline and candidate:

| Value | Both runs |
| --- | --- |
| Registered mainnet genesis | `0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a` |
| `core.DefaultGenesisBlock().ToBlock(nil).Hash()` | `0x6d9420595e38fe399d906b77a75cfd7b276fdee72ff464b163634beee06fd504` |
| Constructed state root | `0x0d8fd6e2278db22ca8ac4f0efc947cb70e11c26f83c6012d741acf3c1b499fe4` |

See the [baseline log](genesis-comparison-v2/baseline.txt),
[candidate log](genesis-comparison-v2/candidate.txt) and
[execution record](genesis-comparison-v2/run.json). This establishes the mismatch
in the current selected recovery source and toolchain before the F11 overlay.
It does not establish its cause, behavior on an older compiler, actual CLI
initialization, or a defect in the backup's stored genesis. Track it separately
as F12 in the [release ledger](../../restart-release-findings.md).

The successful integration fixture instead creates a minimal synthetic genesis
and registers its identity as a test input. `f11MainnetSchedule` temporarily
sets both `params.MainnetGenesisHash` and `params.MainnetChainConfig` and restores
them with `t.Cleanup`; these cases do not run in parallel. Test names containing
`mainnet` refer to the registered-network branch of configuration resolution,
not the production genesis. The genesis equality regression remains failing
and separate; its expected hash was not replaced by the observed value.

The existing supported launch path remains verified restore followed by full
sync. Genesis resync is excluded in the [plan](../../restart-plan.md), and the
[operator kit](../../restart-operator-kit.md) requires the restore marker and
forbids initializing a missing restored chain. F12 needs a reviewed disposition
and final evidence that the supported commands refuse an empty/mispointed data
directory and verify the restored network identity. No genesis correction or
new resync feature is selected by this result.

## Evidence and execution

| Files | Purpose / outcome |
| --- | --- |
| `startup_recovery_test.go`, `config_vectors_test.go`, `config_vectors.py`, `config-vectors.json` | Successful integration fixture and independently calculated serialization vectors. |
| `run.py`, `launch.py`, `qualification-v2/` | Successful integration runner, namespace launcher, exact overlay, environment, command, input hashes, exit code and log. |
| `attempt-1-startup_recovery_test.go`, `run-attempt-1.py`, `qualification/` | Original failed fixture and run. Some failures stop at the genesis prerequisite; others show why the assumed mainnet branch was not reached. The log contains raw non-UTF-8 hash bytes from the original formatting and is preserved byte-for-byte. |
| `genesis_probe_test.go`, `compare_genesis.py`, `launch_genesis.py`, `genesis-comparison-v2/` | Separate baseline/candidate genesis comparison; both executed tests exit 1 on the retained equality assertion. |
| `compare-genesis-attempt-1.py`, `genesis-comparison/` | Initial diagnostic runner wrote a literal backslash-n after JSON. Go rejected its overlays before running tests. Its malformed metadata and parse-error logs are preserved; these are not genesis results. |
| `verify.py`, `verification.json`, `SHA256SUMS` | Evidence checks, their result, and a byte manifest of this bundle. |

The launchers create a private network namespace as root, then drop to the
`rehearsal` user (UID 1000) before executing the tests. Each valid execution
record contains distinct nonempty parent/child namespace IDs and only a down
loopback link. Cached dependencies and offline Go flags are additional limits;
the flags alone are not evidence of isolation or a packet-capture claim.

Commands use two workers, a two-minute test timeout and a seven-minute outer
limit. The runners check the 30 GiB Linux / 60 GiB D: free-space floors and
record capacity. Temporary databases are small test fixtures; no chain backup,
large disk job, public peer, exposed RPC or real-wallet operation is involved.

The previous candidate manifest is checked before execution. Selected source
file hashes are checked before and after; module hashes are checked before.
The evidence verifier also checks the retained overlay inputs and the earlier
state/follow-up/candidate manifests. Historical logs retain their original
paths; the first integration's fixture hash resolves to the archived
`attempt-1-startup_recovery_test.go`.
The original failed log also contains trailing whitespace; `.gitattributes`
exempts that one evidence file from whitespace checks to preserve its bytes.

For another run, make a fresh runner/output location; retained runners refuse
to overwrite their existing Linux result directories. Preserve this bundle and
record any additional fixture changes separately.
