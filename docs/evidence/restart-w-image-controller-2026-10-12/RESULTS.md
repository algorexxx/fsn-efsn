# W-backed replay controller qualification

Eight new image-controller tests and the 32 existing monitor tests passed
(exit 0, 3.905 seconds). The monitor was changed, so these regressions were
relevant. See unit-console-result.json for the explicit console-only provenance
limit. Actual W: lifecycle evidence separately passes wrong-UUID refusal before
child invocation, detach after child exception, fresh reattachment with retained
marker, and clean successful detach. A subsequent real SIGTERM test qualifies
the added termination handler and clean detach. Both test images/markers remain.

The controller keeps one image owner, checks the migrated UUID/backing path,
refuses mount fallback, and monitors local Linux, D:, W: and image filesystem
reserves. Capacity charges database growth to W:/the image; local preparation
retains 21/51 GiB floors, and running reserves stay 20/50/100 GiB. The native
unchanged replay executable checks its image filesystem and D: every batch.
Additional local Linux/W: checks are sampled every 30 seconds. Sampled stops
are not quotas, and forced kill or a storage outage can require manual cleanup.

Resume preparation now hashes before and after the cold checkpoint read and
requires the writable target and read-only checkpoint view to be the same
directory. It omits three redundant full inventories of that same locked,
unchanged directory. Copy-mode checks remain. Runtime source, replay executable,
consensus behavior and release selection do not change.

The next finite test is the 7,170,976 to 7,200,000 image trial. It keeps the
original local checkpoint, backup, independent recovery and baselines; no
production keys or peers are involved. Historical coverage advances only after
replay, both cold checks, preservation verification and storage cleanup pass.
