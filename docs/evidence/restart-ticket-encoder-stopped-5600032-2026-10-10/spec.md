# Read-only inspection after the 15 GiB replay stop

Declared 10 October 2026 before inspection. The requested 6,300,000 replay
remains incomplete. Its stop-before-5,600,033 log supplies the height to inspect,
not an expected hash or proof that the state persisted. Use the existing cold
inspection runner with the attempt/height substitutions and ten prior-preservation
checks (the new tenth check preserves the still-earlier STOP). Retain its diff.
Observer changes only the endpoint literal from 6,300,000 to 5,600,032.

Before hashes, require idle node/replay/observer processes, exclusive run locks
and shared actual LevelDB locks on backup, separate 2,400,000-v2 recovery and
closed working target. Use private mount/network namespaces, loopback DOWN and
read-only views. No writer, database copy, cleanup, W: access, keys or network.
Verify sealed prior evidence, exact executable/source/toolchain and identity.
Read the backup reference before inspecting the stopped target; compare header,
RLP, state/ticket/receipt commitments, bloom, TD and cold ticket reconstruction.
No final warm ticket count exists for this stopped run. Hash closed target before
and after; check backup/baseline metadata and full recovery inventory unchanged.

Require Linux21/D51 GiB before launch and Linux20/D50 GiB before each command.
Build bound7m; each reader3m with2m Go timeout; whole invocation20m+20s kill grace.
Results must total less than256 MiB. Preserve both old failed jobs/STOPs and all
sealed evidence. A passing cold inspection qualifies only this saved endpoint,
not completion of the requested interval or closure of F12/G1. Review actual
capacity and evidence value before another writer; no tiny automatic retry.
