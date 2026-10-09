# Preserved test-profile refusal

Build passed; the read-only check refused with `restored startup: missing restart
anchor`. The test set only the caller configuration copy, while mainnet correctly
uses `params.MainnetChainConfig.RestartAnchor` as its trusted source. This first
check does not establish complete startup readiness. All 56,107 backup file
metadata entries remain equal to the sealed replay inventory. No runtime change
or writable backup access occurred. Fresh v2 corrects only in-process test-profile
wiring and restores the original global pointer on cleanup.
