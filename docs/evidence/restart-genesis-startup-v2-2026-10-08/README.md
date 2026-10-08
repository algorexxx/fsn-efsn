# F12: compiler-dependent ticket compression changes genesis

8 October 2026. The selected Go 1.27.1 baseline executable and the unselected
F11 executable both initialize an empty datadir with a genesis different from
registered Fusion mainnet. Both restart that database successfully and report
network/chain ID 32659. This is a confirmed release-compatibility blocker, not
merely an in-memory probe or an F11 rollback change.

The causal comparison isolates ticket compression for this genesis input:

| Observation | Go 1.21.3 compression | Go 1.27.1 compression |
| --- | --- | --- |
| Identical uncompressed ticket RLP | 252 bytes | 252 bytes |
| gzip.NewWriter output | 246 bytes | 252 bytes |
| Ticket commitment | `0x896244f8418c356094de2772750625998b71ac49fe5d23b87c89f414347c1268` | `0x7015bc16430d0a42a2f7dc2f359fe577c463ac41af6849dacdec9b87329ab1bd` |
| Genesis state root | `0xe6f085ddf1f1e14f3f9a1f1bce498e505c8788370a1b8be5d8463621edd53075` | `0x0d8fd6e2278db22ca8ac4f0efc947cb70e11c26f83c6012d741acf3c1b499fe4` |
| Genesis hash | `0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a` | `0x6d9420595e38fe399d906b77a75cfd7b276fdee72ff464b163634beee06fd504` |

Both streams decompress to exactly the same RLP. Substituting only the old
compiler's compressed bytes in a fresh in-memory genesis, then recomputing the
state root and header commitment, reproduces the entire historical header.
No expected root or header field was assigned to make it match. The comparison
uses the retained [23 September response](../restart-2026-09-23/responses.json),
whose hash agrees with the source's registered mainnet hash.

## Why the compiler affects consensus data

StateDB's calcTicketsStorageData RLP-encodes tickets, then uses the standard
library's gzip.NewWriter. UpdateTickets stores that compressed byte string in
the ticket account through SetData. SetData computes Keccak of those bytes and
uses them as account code. The compressed representation therefore affects both
the header's ticket commitment and the state trie root. The common uncompressed
ticket contents do not make different compressed representations interchangeable.

The same UpdateTickets path is used beyond genesis. This test proves the cause
for the genesis vector; it does not establish which other historical blocks
differ, the first Go version to change output, or a compatible replacement
implementation. Restoring the correct genesis alone cannot establish safe
historical execution or subsequent ticket commitments under the new compiler.

Earlier same-compiler baseline/candidate tests remain valid within their
synthetic scope. They do not address this compiler difference. F11 and the text
dependency experiment are separate unselected changes; neither caused this
observed baseline mismatch. The current Go 1.27.1 artifacts must remain blocked
from release pending compression compatibility qualification.

## Actual startup checks

[run.py](run.py) verifies the existing executable hashes, then builds a small
read-only/construction helper against each source selection. The four actual
console invocations use new disposable datadirs, then reopen those same
datadirs. All report height zero, mining false and automatic buying false.
The generated genesis/config/header identities remain stable across restart.
The commands return zero despite absent restore markers and the wrong genesis.

The [profile](profile.toml) disables public HTTP/WS and telemetry. The probe
additionally disables discovery, peers, IPC, mining and buying. P2P startup is
allowed to bind an ephemeral listener inside the private namespace; there are
no external interfaces and loopback is down. This is not a claim that the node
never creates a socket. No real wallet or backup is opened. Each datadir stays
below 8 KiB in the recorded after-operation samples, excluding executable/cache
files. No bulk restore/replay workload runs.

The four stopped-database inspections use read-only LevelDB. Every database
file's SHA-256 is unchanged across each inspection. Genesis writes the full
and header head markers; the fast marker remains absent/zero at this height.
This is a new synthetic database, not an accepted restored-head readiness pass.

The [first attempt](../restart-genesis-startup-2026-10-08/README.md) stopped at
an invalid explicit empty bootstrap URL before genesis startup. The
[exact correction](fixture-correction.patch) removes those redundant arguments,
uses the profile's empty lists and a fresh output directory, and binds the first
attempt's manifest. No runtime validation or identity expectation was weakened.

## Compression experiment and provenance

[compression_run.py](compression_run.py) uses the unchanged selected node
source with Go 1.27.1 to export its generated ticket bytes. It compiles the
same tiny [compressor](compress.go) under the existing Go 1.21.3 and 1.27.1
toolchains, feeds both the retained identical tickets.rlp file, and preserves
both gzip streams. [ticket_probe.go](ticket_probe.go) verifies equal decompressed
payloads before the in-memory substitution. It does not implement a runtime fix.

The startup run retains 12 successful commands and the compression experiment
retains seven. Both run as the rehearsal user in separate verified private
network namespaces, using cached tools/dependencies, two build workers, bounded
timeouts and the existing free-space floors. These are executable/helper checks,
not new race-test-suite passes. The exact prior executables and candidate overlay
are retained by hash; selected source and earlier evidence stay unchanged.

[verify.py](verify.py) validates 304 prior evidence files, 40 selected
source/module hashes, executable/helper/input hashes, candidate overlay bindings,
both compilers and 54 compression-library source files. It checks every console
observation, read-only file comparison, compression payload and historical header
field. [verification.json](verification.json) records the outcome. Raw logs,
generated bytes, commands, timestamps and environments are retained under
qualification/ and compression/. SHA256SUMS covers the bundle.

## Disposition and next work

Keep F12 open as a G1/G2/G5 release hold. Do not replace the registered genesis,
patch the backup to the new root, waive the mismatch because restore is supported,
or treat successful builds as compiler compatibility. No whole-compiler downgrade,
new compression activation or ticket-format change is selected.

Next, collect a bounded set of preserved ticket byte/RLP vectors and identify a
minimal way to reproduce the legacy compressed representation with a maintained
build toolchain. Compare exact bytes, commitments and state roots, including
ordinary ticket updates and expiry boundaries, before candidate historical
execution. Any compatibility implementation needs a separate reviewed diff,
provenance/license/dependency assessment and appropriate regression coverage.
Genesis equality is one necessary vector, not the whole compatibility proof.

The independent operator issue also remains: an empty/mispointed datadir must
be refused before normal node startup, and restored genesis/anchor/configuration
must match the authenticated release inputs. A restore marker or chain ID alone
is insufficient. Final service commands and their positive/negative startup
tests are still required. F1 exclusions and F11's earlier missing-header-index
behavior remain under their existing reviews; this finding takes priority.
