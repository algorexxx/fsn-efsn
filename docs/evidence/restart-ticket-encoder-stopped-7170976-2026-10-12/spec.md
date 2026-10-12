# Finite read-only stopped-checkpoint inspection

Verify the retained failed attempt and all prior manifests, source/toolchain,
executable/replay identity and separate 2,400,000-v2 recovery. Hold exclusive run
and actual database locks, confirm no replay/node process, and hash only closed
target/recovery files in read-only bind views with private mount/network
namespaces and loopback DOWN. Match exact cold head, full header/RLP, state,
ticket/transaction/receipt commitments, bloom and TD to the backup reference.
Independently reconstruct cold tickets; no final warm count is available.

Require all twelve preservation checks and original failed completion/STOP
unchanged. Start above Linux21/D51 GiB; keep Linux20/D50 GiB running reserves.
Observer build: seven minutes; readers: three minutes with Go timeout two;
outer invocation: twenty minutes plus twenty seconds grace; results <256 MiB.
No database writing, replay resume, cleanup, network contact, real keys, mining,
production activation or release selection changes. Cold verification does not
itself authorize a writer: review capacity and evidence value before another job.
