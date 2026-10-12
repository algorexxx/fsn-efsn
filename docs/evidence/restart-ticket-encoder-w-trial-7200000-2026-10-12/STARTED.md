# W-backed trial dispatched

Started 12 October 2026 at 19:01:11 UTC from prepared commit
`5d05803aaa689a9cdd05f27d14688d7ef6350851`, hidden host PID 33952.
The host runner independently verifies the frozen input manifest
`47c72df6d5bb47a98853cfe97b6b5c977f676003c5f59378eb636db93434602a`.

The correct image is attached as `/dev/loop0` with its recorded UUID and a
dedicated bind mount at `/home/rehearsal/replay/candidate-ticket-encoding-w`.
Runtime startup at 19:01:22 UTC passes the distinct private namespaces,
loopback-down isolation, read-only protected views and mounted capacity gates.
The exact cold inventory and remaining provenance preparation precede any
replay writer. This startup record does not add historical coverage.

One finite job owns the image. Its unchanged replay binary will continue from
7,170,976 to 7,200,000, subject to the declared 46 GiB allocation ceiling,
one-hour clean replay limit and five-hour whole-job limit. The original local
checkpoint and independent recovery remain intact. No additional writer or
live database/image hash is allowed. Do not alter these running inputs.

Runtime status:
`/home/rehearsal/results/restart-ticket-encoder-w-trial-7200000-2026-10-12/status.json`.
Host completion/logs: `tmp/replay-w-trial-7200000-2026-10-12/`.
Require inner `completion.json` and `verification.json`, outer
`storage-completion.json`, host exit and actual detach before final acceptance.
The outer records follow the inner automatically sealed manifest; preserve
them in a separate final report manifest rather than rewriting the inner seal.
