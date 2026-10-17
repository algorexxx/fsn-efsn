# Bounded W-backed continuation toward 13,500,000 started

Dispatched once at 22:50:36 UTC on 17 October 2026 from prepared commit
`ca64525da735aaaa793691d28af4464d25116b4f`. Host PID 113196 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 22:50:48 UTC and was observed at 22:51:05 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 13,200,000 checkpoint has 113,429,663,744 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,536,029,696; D: 56,898,609,152;
W: 3,192,763,407,360; image filesystem 434,853,322,752.
The 118 GiB sampled ceiling (126,701,535,232 bytes) leaves 13,271,871,488 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected. Earlier preparation
refusals remain sealed in their original bundles; this preflight passed.

Prepared manifest: `9cf27264e4cdeea09750fa36eb95ef4721114541f8cc826cdd9d274d9a992e6e`.
Input manifest: `81ae7d3f4dbe76ae1f8f2f3a22e7289a98f3d7b194304245d399283f69ca1079`.
Host runner: `0010eba5ae069a21e937e510730308f927dbe455e85a9e0ebf8555054aec16ad`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
