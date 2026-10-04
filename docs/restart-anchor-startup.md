# Recovery-anchor startup cost

4 October 2026. All 12 cases passed. This closes the bounded local startup-cost
investigation for G2; final release/host timing remains open. It adds only an
opt-in test and evidence. No production anchor, consensus rule or node-runtime change is made.

The original [anchor review](restart-anchor-implementation.md) correctly left
long startup open: each new anchor instance walks stored ancestry and canonical
indexes. `SetupGenesisBlock` and `NewBlockChain` each create one during ordinary
service initialization. Their proof caches do not make the first startup walk
constant-time, nor do those two calls share a proof cache.

## Declared workload and acceptance

The [evidence bundle](evidence/restart-anchor-startup-2026-10-04/README.md)
records the bounds before each run. The first run covers 10,000 and 100,000
descendants; the follow-up covers 1,000,000 without repeating the smaller cases.
At a hypothetical uninterrupted 15-second interval, these are about 1.7, 17.4
and 173.6 days. They are workload comparisons, not a production-rate prediction.

Each depth exercises a disabled-anchor control, aligned persisted heads, split
full/fast heads at half/three-quarter depth, and a wrong canonical index at the
first descendant after the anchor. Each case runs in a fresh child process;
after preparing the expected database digest, LevelDB is closed and reopened
before timing. Both startup calls run in service order. Successful cases retain
all keys and expected heads, and the enabled cases retain anchor readiness.
Both calls must refuse the damaged index without modifying database contents.

The declared limits are 512 MiB per fixture, 120 seconds for the two timed calls
combined, at most `8 * (depth + 1) + 256` stored-header reads, and at most 512 MiB
accounted by Go `MemStats.Sys` after the calls. Logs also retain separate call
timings, cumulative allocation and external command resource accounting. These
are local test bounds, not production service timeout settings.

## Results

The initial eight cases pass in 18.92 test seconds. All four one-million cases
pass in 204.34 test seconds, including preparation, child processes and integrity
digests. Both runners captured zero build and test exit codes.

| Descendants | Aligned startup total | Split-head startup total | Aligned stored-header reads |
| --- | --- | --- | --- |
| 10,000 | 0.340 s | 0.542 s | 40,016 |
| 100,000 | 2.777 s | 3.806 s | 400,016 |
| 1,000,000 | 25.973 s | 37.314 s | 4,000,016 |

The million-descendant fixture occupies 278,726,566 bytes (about 266 MiB).
The damaged-index case at that depth was rejected by both entry points in
28.381 seconds combined, without changing any key/value. The disabled-anchor
control needed four header reads at every depth. These measurements show linear
stored-header work with an anchor. The two aligned startup calls allocate about 12.1 GB cumulatively at the largest depth, while Go's accounted
memory after them is about 63 MiB. Cumulative allocation includes reclaimed
objects and must not be presented as simultaneous RAM demand. The follow-up
command reported a maximum resident set of 98,000 KiB (about 96 MiB).

## Interpretation and remaining work

The bounded measurements do not currently justify expanding the node patch list
with a startup optimization. Keep the explicit ancestry check and allow for its
measured growth when preparing production startup supervision. Repeat on the
selected release and actual host to choose service deadlines. Do not extrapolate
these timings into a promise for an arbitrarily old or large chain.

The test uses synthetic unsigned stored headers and empty bodies with a reused
valid fixture state, not one million executed or correctly sealed blocks. It
measures the anchor/startup paths and database consistency checks. It does not
measure disk opening, complete service startup, remote sync, native execution,
production payload sizes or large compatible-reorganization batches. The OS page
cache is warm; no global cache flush is performed. Linux ext4/WSL runs alongside
the separate baseline replay, so timings include that host's workload.

The unchanged node sources are identified by the evidence manifests and baseline
commit. The toolchain is the existing offline Go 1.21.3 Linux/amd64 rehearsal
toolchain, not a newly approved release toolchain. The original backup and replay
databases are not opened by these tests. Larger reorganization-batch cost and the
final supported release matrix remain separate G2 work.
