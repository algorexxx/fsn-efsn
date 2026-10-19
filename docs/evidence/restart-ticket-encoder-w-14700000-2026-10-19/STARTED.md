# Bounded W-backed continuation toward 14,700,000 started

Dispatched once at 01:23:11 UTC on 19 October 2026 from prepared commit
`b703640322969b12d00c871994760006ac47d51a`. Host PID 217956 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 01:23:26 UTC and was observed at 01:24:01 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 14,400,000 checkpoint has 115,198,595,072 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,259,725,824; D: 55,012,773,888;
W: 3,191,225,147,392; image filesystem 433,084,391,424.
The 120 GiB sampled ceiling (128,849,018,880 bytes) leaves 13,650,423,808 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No time limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected. Earlier preparation
refusals remain sealed in their original bundles; this preflight passed.

Prepared manifest: `b3ff4bbc7016076b17a82859035412bb2c11959fc41bf1c739acbc1e66fd62ca`.
Input manifest: `9d5c7e6dcede43054c4ff8c269c3c59af7841534e9e250d7351d82923154a024`.
Host runner: `b143a12555f9ef4cfc51823b0621e6ea45c8ac6811bc24462c3bbcf2b99d8f92`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
