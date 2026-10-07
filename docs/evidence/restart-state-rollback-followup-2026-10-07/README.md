# Evidence qualification and correction

7 October 2026. This note corrects the interpretation of the run archived in
commit `92c3e634`. It is not a new test run.

Dependency downloads were disabled. The run used the distro default network
namespace; private network isolation was not established, and zero network
activity was not independently verified.

The original `environment.txt` and the text emitted by `run.sh` claim that
network use was impossible because of the Go dependency settings. That claim
is incorrect: those settings do not prevent arbitrary network calls by a
process. The recorded interface listing includes an active network interface.
It does not establish whether the test actually sent or received traffic.

The original runner, environment record, logs, overlays and `SHA256SUMS` are
preserved byte-for-byte. The manifest covers the original 16 run artifacts;
this later explanatory note is outside that manifest. The correction qualifies
the environment claim and does not change the recorded subtest outcomes.

Treat `run.sh` as an archived invocation. It hardcodes this evidence directory
and would overwrite its contents if rerun. Future work must use a fresh output
directory and record the controls actually established. Required isolation
must be verified before executing a test that depends on it.

The [findings report](../../restart-state-rollback-findings.md) records the
bounded result and remaining limits. F11 remains open. No production change,
release approval, historical-compatibility result or network-isolation pass is
implied by this correction.
