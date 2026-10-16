# W-backed continuation to 11,700,000

See [the frozen specification](inputs/spec.md) for scope, limits and acceptance.
This directory contains fresh prepared inputs; completion and verification
records determine the eventual outcome. No production release is selected.
The existing preflight scopes loop checks to the configured image; an unrelated
Docker read-only ISO is allowed. Controller snapshots are unchanged. The host
runner uses a fresh 11,700,000 log directory and captures early errors.

The [first preflight refusal](preflight-refusal-1/FAILURE.md) preserves a
Windows line-ending preparation error. The observer and patch were corrected
byte-for-byte before launch; controller checks and all limits remain unchanged.
