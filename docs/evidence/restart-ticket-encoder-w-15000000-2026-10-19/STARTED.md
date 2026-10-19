# Bounded W-backed continuation toward 15,000,000 started

Dispatched once at 07:22:34 UTC on 19 October 2026 from prepared commit
`141073f20f8d5a4fbd010439f06535bbfff3ef98`. Host PID 33384 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 07:22:46 UTC and was observed at 07:23:26 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 14,700,000 checkpoint has 115,504,537,600 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,192,616,960; D: 56,246,947,840;
W: 3,191,061,850,112; image filesystem 432,778,448,896.
The 120 GiB sampled ceiling (128,849,018,880 bytes) leaves 13,344,481,280 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No time limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected. Earlier preparation
refusals remain sealed in their original bundles; this preflight passed.

Prepared manifest: `2503c4b5562c3800670c5667749c97298df33c9cb90f4b2540f9eca6201b54e2`.
Input manifest: `1a1897fcde80d0f7fdd00120fce73186588a112b7478e4b80ed7d1b05383e17d`.
Host runner: `28b0f7ebac1b7540bc50db1a33a0f3b57e9e11fa3886e58102f6be4cb77fd7b5`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
