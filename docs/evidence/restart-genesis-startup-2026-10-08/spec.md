# F12 startup characterization

8 October 2026. Bounded follow-up to the default-genesis mismatch and the
operator kit's empty/mispointed-datadir requirement. No runtime patch or new
genesis is selected by this work.

Use the existing checksummed P1–P17+B1+D1 executable and the previously built,
unselected F11 executable. For each, start the actual console command once
with a new empty datadir and once with that same generated database. Read
genesis, current head, network identity and mining/buying flags, then exit.
Keep the approved profile's disabled HTTP/WS/telemetry defaults; additionally
disable discovery, peers, IPC, mining and automatic buying for this probe.
Run in a private network namespace with no external interfaces or real keys.

Separately compare direct default-genesis construction, repeated construction
and SetupGenesisBlock in memory under both source selections. A small reader
opens the stopped CLI databases read-only and records their genesis/config/head
identity. Compare database-file hashes around that read. Do not open a backup,
replay database or production datadir.

These are characterization observations, not a test that permits a different
genesis to count as mainnet. The registered hash remains the identity oracle;
record equality or mismatch explicitly. Preserve command failures or surprising
differences before changing the fixture. Require no mining, no buying, genesis
height zero, stable identity on restart and identical database bytes across
the read-only inspection. Report initialization of an empty datadir as a missing
operator-startup safeguard, even if the process succeeds.

Use cached Go 1.27.1 dependencies, two workers, at most seven minutes per build
and 45 seconds per console invocation. Check the existing 30 GiB Linux / 60 GiB
D: floors. Synthetic databases only; no bulk disk workload or public contact.
Retain runner, helper, profile, exact commands, hashes, exits, namespace and
logs in a fresh evidence directory. Actual release/host command qualification
and independent acceptance remain open.
