# Complete-state partition and synchronization diagnostic evidence

Baseline: `92a561bd276158b26dd3af7afa9a61d746907900`. No production source or
dependency changes. The additional test extends the validated participant-entry
fixture with a deliberate competing-producer partition.

The live run **failed before repair**, after 306.24 seconds. Its 150-second
post-heal gate did not find a common advancing chain. Do not read the acceptance
steps below as completed observations. No manual repair was submitted.

`diagnose-linux.sh` subsequently built a separate race binary and audited both
stopped branches, then reconnected fresh services with signing and buying off.
Both 26-block cold ledgers passed. Both stopped heads had equal total difficulty
63,370,514,724 and one connected peer each; automatic sync did not start.
A separate explicit downloader call reached missing historical header
15,085,106 and failed. The diagnostic therefore also exited 1 after 60.69 seconds.
Its before/automatic/after heads and roots are unchanged. Neither run reports
a data race. See [the report](../../restart-full-state-partition.md).

`initial-sources/` retains the original live-run versions of the three relevant
test files. Only the node harness changed afterward, to add optional debug
logging; the cold diagnostic is an additional test file absent from the first
binary. Both binary hashes and build logs are retained. `identities.json` names
the original overrides and the sources of the diagnostic build.

`prepare-copies.py` checks the original compact-state manifest and all 230 source
files, enforces a 50-GiB free-space reserve, and writes two fresh C: copies under
`tmp/full-state-partition-2026-09-26`. It refuses an existing target. All previous
fixtures, evidence and original backup data remain separate.

Use `check-linux.sh build` then `check-linux.sh run` through WSL FusionRehearsal.
The build uses cached offline Go 1.21.3, two workers and race instrumentation.
The run requires a fresh private namespace with only enabled loopback. The
existing guard refuses the host namespace. Packet loss applies only inside that
namespace. Both active miners use public test keys; no real signer is used.

Both copies execute the reviewed three-block recovery followed by the audited
three-block participant funding prefix. That prefix hypothetically contributes
10,000 mature FSN rights plus 2,020.102 liquid FSN from the backup fixture to public
test key 3 through ordinary transactions. It does not establish authorized real
funding or change the agreed one-backup-block launch.

The test warms both live miners, drops loopback IP traffic for 90 seconds while
mining and automatic purchases remain enabled, retains both branches, heals the
network and waits for a stable missing-nonce gap on an advancing shared chain.
After that gate, it would retrieve every missing original through the block-hash RPC
before submitting any repair. Originals are resubmitted sequentially, with
canonical native-success receipts required on both peers. No new transfer,
forced sync, record edit or buyer restart is used to assist recovery.

If the pool rejects an original for insufficient funding, the test records the
exact pinned-head liquid balance, free interval coverage, signed gas budget and
ticket inventory. It permits a bounded wait for an existing ticket's ordinary
return, but does not wait for a nonexistent ticket. It then stops both nodes,
preserves their automatic purchase records, checks both cold canonical databases
and independently audits both isolated branches. An unfunded repair is reported
as a failed recovery test even if those accounting checks pass.

Success requires all missing originals, the exact saved intent, two fresh
automatic successors, matching cold databases and complete interval accounting.
This is a bounded test with compact history; it does not establish full-history
sync, public discovery, power-loss durability or a universal reserve amount.

`artifacts/producer` and `artifacts/verifier` are the separately audited complete
cold suffixes, including each pre-heal branch. They are not a common canonical
result. `cold-*.json` retains their heads, weights, nonces, saved records and
peer diagnostic. `verify-evidence.py` explicitly requires both failures, the
unreached repair gate, successful branch audits, equal advertised difficulty,
the missing ancestry request, unchanged original 230-file export and no runtime
source changes. It generates identities and checksums; `verify-index.py` checks
those hashes and the exact staged investigation scope before committing.
