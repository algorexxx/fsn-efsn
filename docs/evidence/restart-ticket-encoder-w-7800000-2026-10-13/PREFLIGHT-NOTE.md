# Initial preflight refusal

At 10:04 UTC the initial read-only preflight refused because its blanket
no-loop-device assertion also matched Docker Desktop's read-only ISO.
`preflight-refusal.json` records that exact unrelated attachment, with no
matching replay process or image mount. No replay job or database writer
had started, and no attachment was changed.

`preflight-initial.py` preserves that initial guard. `preflight.py` now refuses
an attachment of the configured replay image specifically, matching the
existing image controller's ownership scope. The controller itself, run locks,
database locks, process checks, mounted identity checks and reserve limits are
unchanged. The four cases in `preflight-guard-check.json` exercise the exact
new expression: an empty list and the observed Docker ISO pass, while the
replay image refuses whether read-only or writable. Fresh full preflight is
required before dispatch. This is a pre-dispatch correction, not a retry of
an executed replay or a relabeling of a failed run.
