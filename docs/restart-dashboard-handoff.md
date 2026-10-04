# Dashboard repository handoff — 4 October 2026

Dashboard development now belongs in the independent sibling repository
`C:\Users\Peter\Documents\CODING\fsn-stats`, on branch
`codex/recovery-readiness`. Start with its `docs/recovery-handoff.md`.
Keep this efsn investigation focused on the chain, recovery, operator monitoring
and independent-producer entry. Public dashboard readiness remains G6 before
public use; further dashboard implementation is parked until resumed separately.

All 32 existing dashboard commits are preserved through
`c85d1f9ab6cd13371811a45cedfe2d1258a14f08`, based on
`e2049634802d4a49adadf998853ce6ee6b1158d0`. The standalone clone was verified with
matching commit/tree IDs, 773 byte-identical tracked files and a successful full
Git object check. It has its own object store with no alternates or hard-linked
objects. Only the handoff guide and README link were added after transfer.
That documentation is committed in the standalone repository as `e9cc45f`.
No application change or new test claim is part of this reorganization.

The `upstream` remote names `FUSIONFoundation/fsn-stats`; an organization fork
and writable `origin` are still unselected. Nothing was fetched from or pushed
to GitHub. Dependencies and generated builds were not duplicated.

The prior `tmp/fsn-stats-auth` worktree remains unchanged so existing evidence
and cross-project harness paths still work. Its branch is
`codex/dashboard-telemetry-auth`. The original `fusionfoundation/fsn-stats`
checkout and its pre-existing edits are also preserved. Future dashboard edits
go in the standalone repository rather than either older checkout.

Retain the existing `restart-dashboard-*` reports and evidence here as the
historical audit trail; moving them would break recorded paths and references.
New dashboard development/evidence belongs in its own repository. The
[launch plan](restart-plan.md) keeps the dashboard dependency and remaining
public-use acceptance without prioritizing further dashboard work in this chat.
