# W-backed checkpoint copy verified

Completed 12 October 2026 at 18:20:35 UTC (Linux clock). Both workers,
filesystem check, cold observers, cleanup and host dispatcher exit zero.
All 22,501 files / 47,231,339,260 logical bytes match the sealed 7,170,976
inventory, first while reading the source and again from the destination
after clean unmount, detach and read-only reattachment.

The new image is `W:/FusionRestart/replay-work-7170976-2026-10-12/replay.ext4`,
with 512 GiB virtual capacity, UUID `2fb12ac9-9520-4cab-9414-f1041c4d25de`,
and database subdirectory `checkpoint`. The original local checkpoint remains
at `/home/rehearsal/replay/candidate-ticket-encoding-working`.

Cold reads reproduce the exact header/RLP, hash, state, ticket, transaction
and receipt commitments, bloom and total difficulty of the sealed checkpoint:
7,170,976, 5,031 tickets, 160 transactions and 160 receipts. Both executable
identities and source/destination metadata remain unchanged. The input and
startup manifests verify. Post-job inspection finds no replay/observer process,
loop attachment or copy mount. The first post-job shell inspection lacked `rg`
inside WSL; the recorded Python inspection supplies the successful check.

Copy took about 61 minutes and reattachment verification about 21 minutes;
host elapsed time was about 83 minutes. Host and Linux clocks differ by about
two seconds, so cross-clock timestamp ordering is not an acceptance condition.
The recorded minimum reserves exceed 20 GiB Linux, 50 GiB D: and 100 GiB W:.

This accepts the copied checkpoint. It is not additional historical coverage,
independent restore acceptance, a replay-throughput forecast or power-loss
durability evidence. No replay starts automatically. Next qualify the bounded
image attachment/resource controller and run a short continuation on this image.
Preserve the local fallback, backup, independent recovery, baselines and archives.
