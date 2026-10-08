# Preserved ticket compression comparison

8 October 2026. Seven commands completed successfully, 06:38:30–06:38:48 UTC.
The [pre-execution specification](spec.md), [runner](run.py),
[probe](probe.go), [command record](qualification/run.json) and
[verification](verification.json) define the scope and provenance.

All seven available historical ticket blobs match Go 1.21.3 exactly. Unchanged
Go 1.27.1 matches none. Go 1.27.1 with the old flate implementation supplied
through a test-only overlay matches all seven, including the real
AddCachedTickets commitment check. Both legacy modes also reproduce every field
of the preserved genesis header. The modern compiler can therefore reproduce
these commitments; downgrading the entire compiler is not necessary for these
vectors.

| Historical height | Owners | Tickets | RLP bytes | Preserved / both legacy modes, bytes | Unchanged Go 1.27.1, bytes |
| --- | --- | --- | --- | --- | --- |
| 0 | 1 | 5 | 252 | 246 | 252 |
| 3,600,000 | 91 | 4,549 | 220,721 | 206,466 | 210,210 |
| 8,250,000 | 64 | 4,405 | 213,095 | 196,359 | 199,169 |
| 12,000,000 | 41 | 5,054 | 243,666 | 225,891 | 230,855 |
| 15,129,953 | 8 | 491 | 23,776 | 21,629 | 21,861 |
| 15,130,079 | 8 | 491 | 23,776 | 21,655 | 22,043 |
| 15,130,080 | 8 | 491 | 23,776 | 21,655 | 21,913 |

The seven blobs are distinct. All generated gzip streams decode to the exact
same RLP as the preserved stream; the difference is representation, not decoded
ticket content. Each helper uses one Write followed by Close, matching the
runtime call shape. Source-side RLP decode/re-encode is also exact. The
unchanged modern AddCachedTickets calls return `hash mismatch` for all seven;
the other two modes accept all seven. This checks the actual cache consumer,
not block import or historical execution.

Canonical headers exist at all 24 specified heights. Seventeen ticket blobs
are unavailable in both supported code-key layouts and are explicitly listed
in [verification.json](verification.json). We did not regenerate or treat them
as empty tickets. Available samples do not establish compatibility for missing
heights, expiry transitions or all future ticket sets.

## Isolation and preservation

The exporter validates the preserved genesis and tip before opening vectors.
It reads content-addressed blobs directly and checks their Keccak commitments,
so availability does not depend on an old account-state trie being retained.
The backup was mounted read-only inside private mount/network namespaces;
LevelDB was also opened read-only. The child ran as uid 1000 with loopback DOWN,
offline module settings and no keys, node service or signing.

Before/after names, sizes and modification times match for all 56,107 backup
files (117,170,022,674 logical bytes). Both inventories are retained compressed.
This is metadata equality and an enforced read-only mount, not a fresh 117 GB
content rehash. No large disk workload was used; the retained bundle is about
4.8 MB. Initial free space exceeded the 30 GiB Linux / 60 GiB D: floors.

All 1,192 files in the selected node tree still match its pinned D1 inventory.
The record includes 897 source/module hashes, both compiler identities and
compression sources, the exact overlay, three helper identities, argv, times
and exits. Verification also checks 363 files in 13 preceding manifests.

## Diagnostic boundary and correction

The overlay replaces seven flate runtime files and hides nine modern-only
runtime files for one build. It also includes old decoder code because this
is a whole-package diagnostic. It changes neither installed compiler nor
selected source and is not a configuration to distribute. Modern gzip source
was retained. An encoder-only package with a fixed gzip envelope still needs
implementation, review and qualification; see the
[compatibility worklist](../../restart-ticket-encoding.md).

The first evidence verifier incorrectly expected `go env -json` to report
GOENV as `off`. Both installed implementations return an empty environment-file
path when GOENV=off (cmd/go/internal/cfg.EnvFile); the runner explicitly sets
GOENV=off. The [retained verifier and failure](verification-first/run.json)
and [one-line correction](verifier-correction.patch) preserve this reporting
mistake. All seven experiment commands had already exited zero; none was
changed or repeated to address it.

F12 stays open. No runtime patch, compiler downgrade, activation height, new
genesis or release waiver is selected.
