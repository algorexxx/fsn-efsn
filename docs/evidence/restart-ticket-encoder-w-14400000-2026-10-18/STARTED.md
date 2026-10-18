# Bounded W-backed continuation toward 14,400,000 started

Dispatched once at 19:15:58 UTC on 18 October 2026 from prepared commit
`c7ed4c7286687f84e0bf92b6a7da3d0e8f0b0f9d`. Host PID 75972 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 19:16:10 UTC and was observed at 19:16:46 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 14,100,000 checkpoint has 114,875,281,408 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,328,923,648; D: 55,118,630,912;
W: 3,191,535,604,736; image filesystem 433,407,705,088.
The 119 GiB sampled ceiling (127,775,277,056 bytes) leaves 12,899,995,648 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No time limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected. Earlier preparation
refusals remain sealed in their original bundles; this preflight passed.

Prepared manifest: `07be9ccd26eaee6984af474a69d040a9d986b2f26fb46c612b1b9e5da22f9a20`.
Input manifest: `0c3fea5dd0daf7b5cfd39817fb274bbeb0ce74fd7489db9c58b6066d8fe30501`.
Host runner: `2521fa51413eda02aa73c7267488f2e15580e9205b04ce756fdbc64377003cc7`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
