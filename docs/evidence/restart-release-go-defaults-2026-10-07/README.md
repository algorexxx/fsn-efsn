# Go language and compatibility-default review

7 October 2026. Follow-up to the [x/text experiment](../restart-release-text-2026-10-04).
The production selection remains P1-P17+B1+D1, compiled by Go 1.27.1 with
the main module declaring Go 1.18. The proposed x/text update requires Go 1.25.0
and x/sync v0.21.0; it is still unselected. No historical database or real key
was opened, and no public service was a test target.

Recommendation: continue qualifying the ordinary upstream update, without a
blanket override of Go's compatibility defaults. The source review found no
specific consensus-output change caused by the diagnosed loops. That is a
bounded code-review conclusion, not historical compatibility acceptance.
Keeping a private backport would add a maintained dependency fork and a separate
provenance/distribution burden; reserve it for a demonstrated compatibility
blocker. Neither option is accepted for release yet.

## Scope and inputs

The four retained source copies are unchanged. The earlier report was verified
before and after this work, including manifests, source inventories and release
binary hashes. Diagnostic builds used the experimental node/recovery copies,
the same compiler and `-gcflags=github.com/FusionFoundation/efsn/v5/...=-d=loopvar=2`.
This identifies compiler transformations in compiled project packages, including
code that might be removed by the linker; it is not a runtime call trace.
The diagnostic executables are separate from the retained release experiments.

Builds and tests used a private network namespace with only a down loopback
interface, offline module resolution, two Go workers and deadlines of ten
minutes per build or five minutes per test package/seven minutes per invocation.
The preflight required 30 GiB Linux and 60 GiB D: free. No bulk copy was needed.
The tests explicitly set `GOMAXPROCS=2`; they do not validate automatic cgroup
CPU sizing on the eventual production hosts.

The compiler's own compatibility table/documentation is retained with its BSD
license. The official [module reference](https://go.dev/ref/mod#go-mod-file-go),
[Go 1.22 language notes](https://go.dev/doc/go1.22#language) and
[GODEBUG documentation](https://go.dev/doc/godebug) were also checked. Module
language versions, process-wide library defaults and compiler version are
distinct inputs. Raising the main module's language does not automatically
raise the language version of every unchanged dependency.

## Loop-variable review

The node build reports 25 distinct source loops, involving 26 variables.
There are 27 deduplicated diagnostic records because an inlined `netutil.net`
also appears under its qualified name. The recovery build reports 14 loops
and 15 variables. Its ticket-scoring function has a different line offset
because recovery is a separately patched source selection.

`loops.json`, original compiler output, source hashes and
`loop-source-excerpts.txt` retain all locations. `supporting-source.txt` records
the relevant callees. The following review covers the diagnosed source loops,
not every possible language-version effect or all of x/text's upstream changes.

| Locations in the node copy | Inspected behavior / disposition |
| --- | --- |
| `consensus/datong/consensus.go:857` | `calcDisInfo` hashes the current ticket ID synchronously, then copies the winning TicketBody by value. No pointer to the reused loop variable is retained for scoring. The formula and owner ordering are unchanged. |
| `core/state/state_object.go:375` | Key/value slices are consumed in the current iteration. RLP creates encoded value bytes; SecureTrie hashes the key and copies its preimage. No identified dependence on one reused map variable. State-suite compilation remains a coverage hold. |
| `core/state/statedb.go:1390`, `common/ticket.go:107` | Ticket values/display fields are computed in the current iteration and placed into fresh result values. |
| `core/types/bloom9.go:107` | Topic bytes are hashed synchronously. The repaired complete types suite passes on both versions. |
| `rlp/encode.go:219,235` | Each list header is encoded/consumed before advancing; the writer uses its encoding buffer, not a retained pointer to the loop header. The full RLP suite passes on both versions. |
| `trie/sync.go:314,320` | Keys pass to raw database helpers by value; SyncBloom immediately extracts a uint64 from the slice. |
| `accounts/manager.go:214,228`, `core/bloombits/matcher.go:492` | `sort.Search` invokes the closure synchronously in the current iteration. |
| `cmd/efsn/accountcmd.go:212,256` | Listing formats immediately. The retained match pointer is followed immediately by `break`, so there is no later iteration overwriting it. |
| `eth/filters/api.go:255` | `Notifier.Notify` marshals the current log before returning and buffers JSON bytes, not the passed loop-variable pointer. |
| `core/vm/stack.go:89`, `eth/tracers/logger/logger.go:324`, `internal/ethapi/api.go:968,979` | Immediate formatting/value conversion; no retained loop-variable address found. |
| `p2p/netutil/net.go:93,130`, `p2p/nat/natpmp.go:112`, `p2p/nat/natupnp.go:78,144` | Immediate method calls. The UPnP `VisitServices` implementation invokes visitors synchronously. No real router was exercised. |
| `p2p/discv5/net.go:684` | A lazy diagnostic closure captures the seed variable. The selected CLI uses a StreamHandler whose LazyHandler evaluates synchronously. A different asynchronous custom handler could observe different logging values; do not claim universal identity of diagnostics. This is discovery logging, not ticket consensus. |

These diagnostics are grounds for targeted review, not evidence that each loop
was previously wrong. No production loop rewrite is justified by this result.

## All 22 changed compatibility overrides

The earlier build-info comparison is authoritative for the actual commands.
Both lose the same 22 legacy overrides when the main directive rises to 1.25.0.
The following values describe the resulting Go 1.27.1 defaults, with no operator
GODEBUG override. The retained compiler source/documentation supports the map.

| Setting(s), baseline to experiment | Consequence for the selected operation |
| --- | --- |
| `containermaxprocs: 0 -> 1`, `updatemaxprocs: 0 -> 1` | Runtime can use CPU quotas/affinity and update parallelism. Inspected application/library calls only read GOMAXPROCS for cache work. Check service/container CPU settings and shutdown/cache timing on actual hosts; bounded tests pin this value. |
| `decoratemappings: 0 -> 1` | Linux memory-map annotations change diagnostics. No chain serialization change identified. |
| `gotestjsonbuildtext: 1 -> 0` | Test build errors can be JSON events; CI parsers must accept them. This changes build tooling, not block rules. |
| `httpcookiemaxnum: 0 -> 3000`, `urlmaxqueryparams: 0 -> 10000` | Finite request parsing limits replace unlimited cookie/query parsing. Retain newer limits; ordinary API/proxy acceptance still applies. A blanket legacy default would disable these protections. |
| `httplaxcontentlength: 1 -> 0` | Empty Content-Length headers become errors. Verify legitimate proxy/RPC clients; no reason identified to preserve malformed framing. |
| `httpmuxgo121: 1 -> 0` | ServeMux pattern/routing rules change. Node custom handlers and metrics/pprof use it; root RPC also has its own path check. Earlier node/RPC tests provide partial coverage, not final endpoint acceptance. |
| `httpservecontentkeepheaders: 1 -> 0` | ServeContent removes selected response headers on errors. The compiled-source inventory finds no direct external ServeContent/ServeFile reference; this is not proof of universal unreachability. |
| `multipathtcp: 0 -> 2` | MPTCP is enabled by default for eligible listeners, subject to OS support/fallback. Real-host listening/peer checks remain necessary. |
| `netedns0: 0 -> 1` | Go's DNS resolver sends EDNS0 information. Test the real host resolver and bootstrap DNS; local offline tests do not establish compatibility with those resolvers. |
| `panicnil: 1 -> 0` | `panic(nil)` produces a non-nil runtime panic value. The compiled discovery-v5 source contains explicit invariant panics; generic recover handlers can observe the difference. Do not describe this as an intentional consensus change or preserve old behavior without an actual need. |
| `randseednop: 0 -> 1` | Global math/rand.Seed becomes a no-op. The AST inventory finds no direct reference to it in either command's compiled source set. Calls on explicitly created Rand objects are separate. Ticket ranking uses Keccak, not this global generator; equal-weight fork ties remain nondeterministic. |
| `rsa1024min: 0 -> 1` | RSA operations require at least 1024-bit keys. Relevant to RSA/TLS or generic JWT APIs, not Fusion's secp256k1 ticket signing. Existing node JWT use is HMAC. Check actual service certificates. |
| `tlsmlkem: 0 -> 1`, `tlssha1: 1 -> 0` | TLS defaults add X25519MLKEM768 and remove SHA-1 signatures in TLS 1.2. Relevant to HTTPS/WSS/dashboard connections; test real certificates, proxies and peers that use TLS. Fusion's RLPx peer protocol is not TLS. |
| `x509negativeserial: 1 -> 0`, `x509rsacrt: 0 -> 1` | Certificate parsing rejects negative serials; RSA private-key parsing uses/validates stored CRT parameters. These require certificate/key-format compatibility, not a wallet-balance change. |
| `x509sha256skid: 0 -> 1`, `x509usepolicies: 0 -> 1` | Certificate creation uses newer key-ID/policy behavior. No direct CreateCertificate reference appears in the command dependency source inventories. |
| `winreadlinkvolume: 0 -> 1`, `winsymlink: 0 -> 1` | Windows path/reparse-point behavior. The declared release target is Linux; do not infer a native Windows pass. |

Both commands retain the five overrides `cryptocustomrand=1`, `tlssecpmlkem=0`,
`tracebacklabels=0`, `urlstrictcolons=0` and `x509sslcertoverrideplatform=0`.
Timer/TLS settings already removed in Go 1.27 do not reappear by keeping a
Go 1.18 directive. That directive never reproduced the entire old runtime.

`references.go` parses the GoFiles/CgoFiles in the retained command dependency
inventories for selected package-qualified references. It is an aid to review,
not whole-program reachability or reflection/foreign-code analysis. Imported
library helpers can be compiled without being reachable in the final command.

## Verification and test-only repair

The original tests were run before editing. Both versions had identical
core/types compilation failures: a removed `tx1.data` diagnostic print and
a missing base-fee argument. Patch `10-core-types-fixtures.patch` removes the
three unasserted diagnostic prints, supplies `nil` for the existing legacy
transaction fixture's absent base fee, and preserves the block-time literal
as the current uint64 API type. The existing wire/hash expectations remain.
No transaction, receipt, block, or consensus implementation changes.

The two repaired test files are in the investigation workspace. Go overlays
applied their exact same bytes to both immutable source copies. They are a
separate test-only patch, not a production D2 addendum.

| Check | Baseline / experimental result |
| --- | --- |
| Both diagnostic command builds | Pass; source copies unchanged |
| Common package, race | 16 top-level tests pass each, no skips |
| RLP package, race | 33 top-level tests/examples pass each, no skips |
| Repaired complete core/types package, race | 21 top-level tests pass each, no skips; both 2.200 s |
| Original core/state package | Identical compile failures after dependencies are cached: removed memory-database APIs, asset-aware balance signatures, new state/ticket root arguments, DumpConfig and others |
| Earlier experiment/input re-verification | Pass; manifests and original candidate binaries unchanged |

Preserved setup failures distinguish missing cached test libraries from source
failures. Public downloads ran only from an empty directory through the Go
proxy/checksum service. One transitive download mistakenly requested
go-internal v1.9.0; the manifests require v1.6.1, which was then downloaded and
used. No manifest was changed and v1.9.0 is not selected. All failed offline
attempts and download metadata remain. An initial support-excerpt script used
an incorrect module path; the corrected paths come from the dependency inventory.

## Decision and remaining boundary

This completes the bounded language/default inventory and the core/types test
repair, while retaining F1/F10 holds. Do not add `godebug default=go1.18` or
global legacy compiler flags to make the language upgrade appear smaller:
runtime-default overrides do not restore old loop semantics and can restore
less protective networking behavior.

Next, port the relevant state tests and console/tracer fixtures, and resolve the
missing RPC fixtures or approve precise replacement coverage. Then compare
historical execution and the recovery/handover fixtures on the exact proposed
upgrade before selecting it. Reuse earlier passing checks unless the accepted
source/inputs change. Actual DNS/TLS/service checks belong to the existing
host acceptance rows, not a new infrastructure project.

The WebSocket advisory/version discrepancy, lower-level dependency dispositions,
CI inputs, unchanged baseline replay beyond 3,600,000 and independent review
remain in the consolidated plan. This report adds no consensus redesign or
new launch milestone. `report.py --check` verifies the derived review against
retained inputs; SHA256SUMS covers the evidence except itself.
