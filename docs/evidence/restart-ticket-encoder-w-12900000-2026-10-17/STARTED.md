# Bounded W-backed continuation toward 12,900,000 started

Dispatched once at 10:44:38 UTC on 17 October 2026 from prepared commit
`f427a7e6d816d6687fc05f97cf28c85faf6f9a7f`. Host PID 122820 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 10:45:03 UTC and was observed at 10:45:10 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 12,600,000 checkpoint has 111,883,128,832 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,645,253,632; D: 57,168,334,848;
W: 3,265,272,512,512; image filesystem 436,399,857,664.
The 117 GiB sampled ceiling (125,627,793,408 bytes) leaves 13,744,664,576 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected.

Prepared manifest: `a1f871d803327e8266965962deb119946678001621d63e3213fcc8c99f43e6b7`.
Input manifest: `385056b526fe4fed538acf75da8876becc499205de5547dbadedebcd28186418`.
Host runner: `50b160724fde2f9074d90cae1f08f7ca76c8817ea5bc78651518b56cb5b3ab2f`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
