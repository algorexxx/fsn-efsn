# Bounded W-backed continuation toward 14,100,000 started

Dispatched once at 13:05:57 UTC on 18 October 2026 from prepared commit
`0b662d09af6b150f66e2a503682cfb10e4e68cb1`. Host PID 99992 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 13:06:10 UTC and was observed at 13:06:47 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 13,800,000 checkpoint has 114,461,392,896 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,404,408,832; D: 56,796,876,800;
W: 3,191,772,095,488; image filesystem 433,821,593,600.
The 119 GiB sampled ceiling (127,775,277,056 bytes) leaves 13,313,884,160 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No time limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected. Earlier preparation
refusals remain sealed in their original bundles; this preflight passed.

Prepared manifest: `db612c1df746410e8d623dbac80be24abb5f8e85983d02f232c0b1947fe0d20e`.
Input manifest: `ea03064094085c9fc5e91d488dc15de9b31942ce00c6825e0b19e3cdd37ec6f6`.
Host runner: `4255e87160ffb0606f96c8018cc38ec5df18ea46fe55fd47f325d532d5050124`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
