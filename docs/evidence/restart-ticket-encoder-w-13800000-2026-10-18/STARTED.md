# Bounded W-backed continuation toward 13,800,000 started

Dispatched once at 06:00:49 UTC on 18 October 2026 from prepared commit
`2041f820144d75bf46c50d8506b2d7b08f5f6182`. Host PID 209556 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 06:01:00 UTC and was observed at 06:01:35 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 13,500,000 checkpoint has 114,067,230,720 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,465,365,504; D: 56,884,977,664;
W: 3,192,229,929,984; image filesystem 434,215,755,776.
The 119 GiB sampled ceiling (127,775,277,056 bytes) leaves 13,708,046,336 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No time limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected. Earlier preparation
refusals remain sealed in their original bundles; this preflight passed.

Prepared manifest: `0d47b191da4a5edad183b3228b32472ff3504bb3c5624836dc8c5d5903e45a90`.
Input manifest: `0b0c9b6aa76c800f3128444cd6a3d5f6d85d4fecd29a6d2047b0330a992b15a3`.
Host runner: `a65f92c58837b5148b2fa74d6326b43e79ef50b47767151ca18c82323bfd200f`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
