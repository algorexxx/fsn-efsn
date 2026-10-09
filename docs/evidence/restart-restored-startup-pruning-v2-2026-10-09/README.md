# Complete synthetic ancestry and normal pruning

Prepared 9 October 2026. Pending execution.

This bounded follow-up checks whether the unselected restored-startup candidate
starts, imports one local block, stops and restarts in normal pruning mode with
all ancestors present. The earlier sparse, late-height fixture lacked ancestors
used by `BlockChain.Stop`; its failed run and archive-mode follow-up remain intact.

Use the identical retained candidate CLI and its existing test-only profile shim.
Only a new test seeder is compiled through a Go overlay; no runtime source or
release selection changes. A fresh synthetic genesis uses public test key 1,
132 genesis tickets, chain ID 32659 and all configured EVM forks at genesis.
Build/import blocks 1–129, retain child 130 as local RLP, and bind the test anchor
to 129. This is synthetic startup/lifecycle evidence, not mainnet history or
post-legacy consensus qualification; the CLI's legacy checkpoint range still
applies at these low heights. No real key or public mining is involved.

Run as the rehearsal user in a separate network namespace with only loopback
down, no dialing/discovery/RPC, mining and auto-buy disabled. One Go worker,
nice 10; seeder build <=5 minutes, seed <=90 seconds, each CLI <=45 seconds,
cold observation <=45 seconds, each with a ten-second kill grace. Before each
command require >20 GiB Linux and >50 GiB D: free; preparation requires one
additional GiB. Fresh test output must stay under 256 MiB, sampled between
commands. No replay, backup or recovery database is opened or hashed.

Pass requires exact expected heads, roots and ticket commitments; clean exit
and shutdown writes for HEAD, HEAD-1 and HEAD-127; successful local child import;
fresh-process restart; read-only cold checks of all three retained state roots;
unchanged retained source/CLI identities and cold database bytes during inspection.
Preserve failures, inputs, command logs, identities, namespaces, resources and
verification. Do not repeat the 19 existing refusals or four archive-mode cases.

This fresh attempt changes only the seeder log to render the child hash as hex.
The first attempt built and seeded successfully, then its strict UTF-8 log reader
refused the raw hash bytes produced by Go formatting. No CLI phase ran. The
failed input, runtime directory and raw logs remain in the sibling first bundle.
