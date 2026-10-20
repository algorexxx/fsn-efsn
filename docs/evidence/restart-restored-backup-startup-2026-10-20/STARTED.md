# Complete-backup startup qualification dispatched

Dispatched once at **02:02:50 UTC on 20 October 2026**, host PID 35480,
from prepared commit `e51fb59b`. The atomic dispatch claim prohibits retries.
The input manifest is
`bc33b0a0378c8a414cd51e2c020dd255a0e87102ab80837d8e36ed33758e905d`.

Startup gates pass: sealed inputs, exact CLI/source/profile identities, original
backup metadata, protected fallback/recovery metadata, final replay image stat,
capacity and absence of other test processes or loop devices. The private network
namespace differs from its parent and contains only loopback DOWN. The original
backup is bound read-only; only the disposable image is attached read-only,
with its verified UUID. The first phase rechecks all original closed hashes.

`startup-observation.json` is a fixed snapshot of the latest resource/progress
sample. No writable phase or completion is claimed by this startup record.
The source and final replay checkpoint remain protected. After the initial hash
phase, the finite runner performs startup/restart, detach and cold verification.
The whole-job cap is eight hours; CLI invocations are each capped at ten minutes.

`START_SHA256SUMS` seals only these completed startup records, excluding live
progress, command output and later completion records. Inspect completion,
verification, cleanup, resource and host records before any dependent work.
Do not launch a second owner, hash a live database or repeat unchanged tests.
