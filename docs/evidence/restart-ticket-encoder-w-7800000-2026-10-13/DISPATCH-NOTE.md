# Dispatcher log-path correction

The original hidden dispatch at 10:06:50 UTC exited before creating a runtime
or attaching the image. Its frozen launcher still named the previous host log
directory; that directory exists, so the first guard refused without writing.
The original hidden console was not captured. Running its validation prefix
separately reproduced `Preserve existing host job records`; the complete script
was not run again. Read-only process/attachment inspection found no test process
or replay image, only Docker Desktop's unrelated read-only ISO.

The original `run-host.ps1`, preparation seal and `dispatch.json` stay intact.
`run-host-v2.ps1` changes exactly one host log-directory path. Inputs, controllers,
checkpoint, identity, reserves and finite limits remain byte-identical.
`DISPATCH_V2_SHA256SUMS` separately seals this correction. Dispatch v2 requires
fresh validation and checks that its own host records are absent. This is a
corrected launch after refusal, not a retry of a database execution.
