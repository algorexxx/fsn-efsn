# Selected-release networking fixtures and dependency review

4 October 2026. Continue F2/F3 and F10 from the release findings ledger, using
the frozen P1–P17+B1 production selection and Go 1.27.1. No production protocol
or consensus change is selected by this work.

## Declared scope and bounds

Repair the two demonstrated test problems: deterministic parser rejection and
structured Go URL errors; signed Fusion discovery fixtures with unchanged RLP
payloads, expected decoded fields and signer identity. Retain all original
vectors and before/after tests. Generate replacement packet envelopes separately
from the production packet encoder/decoder; changing the authenticated type
requires resigning. Existing public test keys only.

Use a new small source copy of the exact selected node. Overlay the repository's
matching discovery tests (including existing P10 test-loop startup) and only
the new test corrections. Run the two focused cases first, then the discovery
package with race detection because these were its known failing fixtures and
the selected compiler changed. Each run has a three-minute test/five-minute
outer deadline. Tests run in a private network namespace with only loopback up.
No blockchain data or real keys are opened.

Install pinned official `golang.org/x/vuln/cmd/govulncheck@v1.8.0` outside the
project dependency graph. Record its module sums, compiler and binary hash.
First scan both retained selected executables without running them. Binary-mode
results identify vulnerable symbols, not runtime call paths or exploitability.
If needed, run source-mode analysis for these two commands to refine findings;
keep source manifests read-only and record any required dependency metadata
downloads. Each scan has a ten-minute deadline and two Go workers. Parse actual
findings: JSON-mode exit zero alone does not mean a clean scan.

Keep at least 30 GiB Linux / 60 GiB D: free before preparation. This is small
source/compiler-cache work; no further history copy. Do not upgrade project
dependencies automatically or suppress findings. Record concrete affected
components and next actions in F10, preserving the original scan output.

References: [govulncheck documentation](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
and [Go vulnerability management](https://go.dev/doc/security/vuln/).

## Completed results

The two original failures reproduce against the selected production tree with
the matching discovery-test overlay. `07-discovery-fixtures.patch` corrects only
`node_test.go` and the six hex vectors in `udp_test.go`. The parser test uses a
deterministic unavailable resolver and checks structured `url.Error` fields;
valid literal identities and rejection cases remain. Packet types change from
Ethereum 1–4 to Fusion 40–43, requiring new authenticated envelopes. All RLP
payload bytes, trailing fields, expected decoded objects and signer identity
remain unchanged. `convert-vectors.go` uses the existing public test key and
does not call the production packet encoder/decoder.

Focused parser, node-string and forward-compatibility tests pass with race
detection in 1.041 s. The package run passes in 22.725 s. It explicitly skips
`TestRestartPeerAddressLive` and `TestRestartDiscoverySelfLive`, whose opt-in
live-network fixtures were not enabled in this loopback namespace. These skips
are not new live-network passes. Production source/module inventories remain
unchanged; no full-project test pass or final R7 acceptance is claimed.

Four completed dependency scans retain raw streaming JSON, stderr, exits,
start/end times and namespace state. `review-results.py` parses the streams
and produces `scan-summary.json`; `--check` validates it without replacing it.
All scans exited zero with empty stderr, but the node has four IDs with symbol
findings. The recovery binary has one, while its command source has no call
finding. Lower-level findings are retained. See the
[dependency report](../../restart-release-dependencies.md) for code review,
the unreviewed WebSocket fixed-version discrepancy and remaining release holds.

## Approval rejection and offline execution

Automatic approval review rejected the proposed online binary scan because it
could export binary-derived module metadata to `vuln.go.dev`. That scan did not
execute. The scanner's earlier `-version` invocation only obtained public
database-version metadata; it did not analyze a project artifact.

The approved safer alternative used the official
[complete public download](https://go.dev/doc/security/vuln/database) at the
fixed URL `https://vuln.go.dev/vulndb.zip`, independent of any project metadata.
The 3,398,564-byte archive has SHA-256
`a601a35d09bb8daee2acea8c7944b1964df1d87f4f3611efd2ee754b5e470f39`;
the database is dated 1 October 2026, 20:24:15 UTC. The scanner and complete
database remain under `/home/rehearsal/results/restart-release-followup-2026-10-04`.
The archive is not duplicated in Git; returned advisory records are retained in
the raw scan streams. `database-snapshot.json` pins download provenance.

Both scan scripts ran as user `rehearsal` under `unshare --net`, with no enabled
interface and a local `file://` database. Source scans additionally disabled
module proxy/checksum downloads. No source or binary-derived module metadata
was sent externally; the rejected online action was not retried.

## Verification and reproduction

`test-inputs.json` pins the 13 baseline discovery test files from commit
`9c64e55f1da13b290d885c3faf9d42876701aa14`, the separate patch and corrected
file hashes. `network-source-inventory.json` pins the entire tested source.
`verified-inputs.json` confirms all three retained source trees and exact node,
recovery and scanner binaries after analysis. It also verifies modern gofmt and
shell syntax. `SHA256SUMS` covers every evidence file recursively except itself.

For read-only verification on the retained host, run `review-results.py --check`.
`verify-inputs.py` additionally checks the retained WSL source/binary inputs and
rewrites only `verified-inputs.json`. The workload scripts intentionally refuse
to reuse their fixed completed destinations. A new run needs separate paths,
the same pinned inputs and the declared bounds; do not overwrite these results.
Do not run the network scripts outside their declared isolated namespaces.
