# Explicit stopped-checkpoint continuation

Four targeted controller tests pass, including acceptance of the real verified
5,331,360 inspection without changing the failed 5,400,000 completion, rejection
of 19 missing/mismatched provenance variants and each of 12 failed preservation
checks, and the existing successful-prior and path/recovery guards. Unchanged
monitor process tests were not rerun. The saved patch and source hashes identify
the tested Python controller; the efsn runtime and replay binary are unchanged.

The job/verifier validate the stopped inspection explicitly, find source/binary
in the original attempted run, and preserve/recheck its STOP hash. Read locks on
actual LevelDB LOCK files guard preparation/cold/final hashes. The working lock
is released before the retained replay binary starts; exclusive run locks remain.
A real new continuation must still pass full preflight, replay and cold evidence.
