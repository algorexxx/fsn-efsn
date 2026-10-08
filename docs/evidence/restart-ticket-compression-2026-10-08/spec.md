# F12 historical ticket encoding comparison

This is a bounded, offline characterization of the frozen P1–P17+B1+D1 node
source, not a release patch or a historical replay. No real keys or signing.

Export canonical headers and their content-addressed compressed ticket blobs at
exactly the 24 heights listed in probe.go. These span genesis, early history,
the previous replay boundary, protocol boundaries and the backup tip. They do
not constitute an exhaustive or statistically representative sample. Missing
blobs are recorded as unavailable; never substitute regenerated data. Require
the preserved genesis and tip identities before reading any vector.

Open the verified backup once, using read-only LevelDB through an enforced
read-only bind mount inside private mount and network namespaces. The child
runs as rehearsal, with only loopback DOWN and dependencies offline. Record
database metadata before and after; this is not a full-file content rehash.
Require the preservation marker, >30 GiB Linux and >60 GiB D: free. No bulk
copy or replay. Cap each compressed blob at 8 MiB and decoded RLP at 16 MiB.

For each available vector require header identity, Keccak(blob) = MixDigest,
successful gzip decode and exact ticket decode/re-encode identity. Historical
bytes and header commitments are the independent oracles; do not introduce
expected output bytes from the encoder under test.

Compile the same helper in three modes: Go 1.21.3, unchanged Go 1.27.1, and
Go 1.27.1 with a test-only overlay of all seven Go 1.21.3 flate runtime files
(the nine modern-only runtime files are hidden). The overlay leaves modern
gzip source in place. Never edit either installed compiler or selected source.
The broad flate overlay is a diagnostic, not a proposed shipping configuration.

Each process reads the same exported vectors, compresses each RLP with exactly
one gzip Write followed by Close (matching calcTicketsStorageData), and records
exact byte equality, commitment equality and the real AddCachedTickets result.
It also constructs default genesis in memory. Decode each generated stream
independently with Python; compare every field of generated genesis to the
preserved header. Differences are observations, not harness failures. The
legacy modes are compatible with a sampled vector only if all these checks
match its preserved bytes. No claim about all history follows from a pass.

Record sources, toolchains, overlays, helper hashes, command arguments, exits,
timestamps and both successful and failed attempts. Use fresh result paths.
Timeout builds at seven minutes each and probes at two minutes. Do not change
production runtime, activation configuration or release inputs. Expiry-derived
vectors, writer-only packaging, full replay and independent review remain later
qualification requirements.
