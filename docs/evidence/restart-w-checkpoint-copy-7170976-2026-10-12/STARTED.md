# W-backed checkpoint copy dispatched

Dispatched at 2026-10-12 16:57:42 UTC from prepared commit
`e3431256e39ce21c70817a123da1e75872d713ee`, hidden Windows host PID 33476.
The five-hour outer limit ends around 21:57 UTC (plus kill grace).

Startup identity/capacity and isolation checks passed. The new 512 GiB virtual
raw image was created only on W:. Its exact loop backing identity was checked,
and ext4 formatting completed with exit 0 at 16:58:32 UTC. Initial Linux/D:/W:
free bytes were 23,549,861,888 / 61,227,098,112 / 3,644,338,484,224.
The local 7,170,976 checkpoint is retained behind run/database locks and a
read-only source view. This is a copy/verification job, not chain replay.

Completion and cold destination acceptance are pending. Do not hash a live
destination, start another writer, or infer success from the formatting result.
Read progress.jsonl and the final completion/cleanup/host records on the next
heartbeat. On failure, preserve partial output and inspect before retrying.
The startup manifest seals only already-closed startup records, not live logs.
