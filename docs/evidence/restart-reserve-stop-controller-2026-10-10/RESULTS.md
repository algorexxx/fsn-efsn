# Native reserve-stop continuation gates qualified

Four targeted controller tests pass: two retain prior STOP-based acceptance and
refusal behavior, and two use the actual verified native-reserve inspection to
accept its distinct evidence and refuse missing/mixed/malformed provenance.
Mutated preservation and identity cases remain refusals. Source hashes are
unchanged across both executions. No chain database was opened by these tests.

Only offline test-controller files changed. Native host-reserve stops preserve
the exact failed completion/log/run identities and qualified cold discovery,
without manufacturing a STOP file or reclassifying the failed job as complete.
Physical evidence hashes and STOP absence are rechecked on prepare, finalize
and result verification. Existing completed-job and STOP-based paths remain.
Replay executable, runtime source, limits and release selection are unchanged.
