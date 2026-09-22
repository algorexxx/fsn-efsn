# Historical gateway recovery: 22 September 2026

Evidence: operator-provided Ubuntu console output. This is a smoke test, not a
full-chain audit. The preservation backup remains on Windows.

- Ubuntu 24.04.1, 4 vCPUs, approximately 16 GiB RAM, 200 GiB virtual disk on ESXi
  datastore system5. Filesystem had 67 GiB available after restoration.
- 56,107 source and destination files; all SHA-256 checksums matched before first
  successful startup. The running working copy is subsequently writable.
- Client: Efsn 5.0.3, recovery commit a9fa178, built with Go 1.21.3.
- Chain ID: 32659 (0x7f93).
- Genesis: 0xc2422b1d9d16331be2a5b207c0783027d4419498003f729f4b9e9c5c1838623a.
- Recovered header, full-block and fast-block heads: 15,130,080 (0xe6dde0).
- Head hash: 0xe93ffded087a79097d4309c7831690161db6ed136f4b1a22c4c83a99db80f99f.
- Head timestamp: 2025-10-07 08:43:50 UTC.
- RPC reported zero peers and mining false.
- Blocks 1 and 1,000,000 were readable; block 1 links to the expected genesis.
- Head transaction 0xd85a2c32d72c0ece382abc181574a666b6c75e99a5cb19861633e24f33bd706d
  and its successful receipt agreed with the recovered head.
- Block 1,000,000 transaction receipt
  0xc1e954bc60b2fbd79aed5b5b7fa083284fef870d3420e746e8d902fc902eb235 matched block hash
  0x4b0d0d5a0739c801c3d4fe91258d3b9ddf81f471464e221921442ea503d711a6 and succeeded.
  Both sampled receipts contained Fusion-specific logs.
- A balance lookup for 0x0b5d3768772ece935b5743f1be1a1304b7d47699 at the head succeeded.

The original bootstrap parser rejected an empty bootnode argument. Omitting it
loaded default Foundation hostnames, whose resolution also failed. Commit a9fa178
uses the existing empty-entry filtering helper to support an explicit empty list;
the image build gates on a Go regression test.

Docker did not activate the requested localhost port publication on the internal
bridge. Direct host access to the container IP with Host: localhost worked. The
private RPC proxy from manager commit 846fa28 was then verified live on Ubuntu:
RPC returned the same head, and ss showed only 127.0.0.1:9000. A Windows SSH
local forward was independently tested from the Windows workspace: chain ID,
head, zero peers, and mining false all matched. See [endpoint operations](gateway-endpoint.md).

Not established: complete block/receipt coverage, historical state availability,
trace support, Fusion-specific RPC coverage, or indexer compatibility. The sampled
head is the backup's head, not proof of the final canonical network block. Storage
controller errors observed on the ESXi host remain unresolved; retain the original
backup and avoid assuming this VM is the preservation copy.
