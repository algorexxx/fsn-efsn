# Final bounded W-backed continuation toward 15,130,080 started

Dispatched once at 13:41:51 UTC on 19 October 2026 from prepared commit
`968e978bc59fbacc6ae209e886fae90d9c92ddc1`. Host PID 48340 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 13:42:02 UTC and was observed at 13:42:51 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 15,000,000 checkpoint has 115,777,589,248 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record. Its final 130,080-block range
ends at the preserved backup tip, 15,130,080.

Mounted free bytes: Linux 23,123,898,368; D: 56,210,247,680;
W: 3,190,917,478,400; image filesystem 432,505,397,248.
The 120 GiB sampled ceiling (128,849,018,880 bytes) leaves 13,071,429,632 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No time limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected. Earlier preparation
refusals remain sealed in their original bundles; this preflight passed.

Prepared manifest: `9a9cda2d76d13d996b98d9636e485daf9b3714b4e190b7fd3fc1985afb2c222e`.
Input manifest: `037a12d5aadcf4d651f8ba8e59c6f0e137200e1bda509b7908a30fd5972047d0`.
Host runner: `8112d48d377fbb3c66fe16251d93e7748ac9af0af8fd32a631fe93988b36fa44`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit. Then review the remaining restored-startup, identity-refusal,
recovery, handover and independent acceptance gaps. No release selection or
activation is authorized.
