# Discovery investigation evidence

See the [report](../../restart-discovery-resilience.md) for the results, operating
procedure and proposed independent-discovery work. Baseline is `0df4014`; the
affected discovery runtime files had no changes from original `master`.

| Evidence | Result |
| --- | --- |
| `initial-race.txt`, `initial-test.go.txt` | Initial fixture had mismatched ephemeral TCP/UDP ports and timed out. It also exposed the inherited initialization race. |
| `baseline-race.txt` | Corrected fixture; connectivity assertions completed but race detection failed, 60.92 seconds. |
| `current-race.txt` | Identical corrected fixture with P10; ten leaf cases pass with race detection, 30.44 seconds. |
| `package-race.txt` | Full discovery/P2P suites fail in three legacy tests; no full-suite success claim. |
| `package-baseline-failures.txt` | The same three tests fail with pre-P10 runtime/table-test sources overlaid. |
| `package-focused-race.txt` | Discovery table/bucket/UDP and P2P dial/server tests pass, 14.330 / 1.113 seconds. |

`check-linux.sh` builds and runs the opt-in rehearsal in a private WSL network
namespace with only enabled loopback. The fixture uses a local DNS responder and
public deterministic keys 1–5, never the restored chain or real signing keys.
Use `current` for the corrected production sources. For `baseline`, first run
`prepare-baseline.py`; its small Go overlay restores the two production files
and their direct table-test callers from `0df4014` without modifying the worktree.
The retained baseline run occurred before the production correction was applied;
the overlay provides the equivalent reproduction afterward.

`check-packages.sh` runs the full package suites. `check-package-boundaries.sh`
runs the three known failing tests using that overlay, then the relevant passing
tests using current sources. Its `failures-only` argument omits the second step.
All scripts overwrite their named logs; preserve this capture before rerunning.
The initial fixture and binary are retained as evidence, not as the supported
runner. Builds use the existing offline Go/module cache.

`write-identities.py` verifies outcomes and the narrow production diff, records
source/binary hashes and writes `SHA256SUMS`. `.gitattributes` preserves raw
evidence bytes. The checksums exclude their own manifest. Local ignored binaries
are reproducibility artifacts, not release binaries.
