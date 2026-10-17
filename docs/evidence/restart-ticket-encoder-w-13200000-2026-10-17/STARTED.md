# Bounded W-backed continuation toward 13,200,000 started

Dispatched once at 16:56:18 UTC on 17 October 2026 from prepared commit
`fa3f656b4ff0f3816a1e7e428506a4be10b5b9b5`. Host PID 213744 is alive; host
and early error logs are empty and no host completion record exists.
Mounted startup began at 16:56:29 UTC and was observed at 16:56:48 UTC.
The job uses UID 1000 in private network/mount namespaces with only loopback,
down. The expected W: image and UUID match, and all actual capacity gates pass.

The verified 12,900,000 checkpoint has 112,823,578,624 allocated bytes.
Actual startup allocation equals that preceding closed measurement. This
observation does not establish content equality: the unchanged exact file-hash
inventory gate must pass before replay. The job is performing that preparation;
no new blocks are verified by this startup record.

Mounted free bytes: Linux 23,584,026,624; D: 56,962,572,288;
W: 3,193,322,385,408; image filesystem 435,459,407,872.
The 118 GiB sampled ceiling (126,701,535,232 bytes) leaves 13,877,956,608 bytes
of declared growth headroom. Running floors remain 20 GiB Linux/image,
50 GiB D: and 100 GiB W:. The entire job has an eight-hour cap plus 20 seconds;
clean replay remains six hours, Go 6h15m and replay outer 6h30m. Samples remain
30 seconds. No limit or preservation check changed, and no duplicate writer
was started. Original backup, separate recovery, local fallback, baselines,
archives and failed/sealed evidence remain protected.

The first preflight refused a misnamed observer patch before attachment or
dispatch. Its original preparation and checks are preserved in
[preflight-refusal-1](preflight-refusal-1/FAILURE.md). Correcting that filename,
regenerating its input seal/runner pin and repeating the unchanged preflights
passed before this single dispatch. No controller or content gate changed.

Prepared manifest: `2692f8389e6b1558492120f7f77af72b2cb9ef8407322ff9e6587f2f868a2f97`.
Input manifest: `f011e245be4c55a27c6cc8ab1d21536a80cde52fb0784a6460d799f9207ada58`.
Host runner: `7da5b60f83aa075fa5d6835878ae36699d7bdeb01d6893aa6b82a6b18fc2e3f6`.
START_SHA256SUMS seals this record, dispatch, startup observation/capture and
the prepared manifest. Final success requires inner verification, outer image
cleanup and host exit; no release selection or activation is authorized.
