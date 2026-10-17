# Preflight refused a misnamed observer patch

The read-only preflight at approximately 16:54 UTC on 17 October 2026
stopped in replay_monitor.require_observer_change: the required
inputs/observer-change.patch was absent. Preparation had incorrectly written
the same canonical diff to inputs/details.patch. Host checks had passed;
no image attachment or test was dispatched, and preflight.json was not written.

The tool returned FileNotFoundError at preflight.py line 28 / replay_monitor.py
line 81, naming inputs/observer-change.patch. These are the original prepared
inputs and host checks. Correct only that filename, regenerate the input seal
and its runner pin, then repeat both preflights. Keep every controller and
acceptance gate unchanged. This is a preparation refusal, not a replay failure.
