# Stopped checkpoint at 6,623,296

Prepared read-only inspection of the stopped 6,900,000 job. Its retained STOP
records three failed size measurements. All failures report disappearing .ldb
files during du traversal, consistent with concurrent LevelDB compaction. The
stop-before-6,623,297 log supplies a proposed inspection height, not proof of a
persisted head. The original failed completion remains sealed and unchanged.
No additional coverage is accepted until this inspection and verifier pass.
