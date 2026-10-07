# Initial candidate qualification

The first parameter-package run failed one test expectation, before either
build ran. The selected source tags `DAOForkSupport` with `omitempty`; a false
boolean therefore has no JSON field. The initial literal incorrectly included
that field. The corrected literal follows the selected struct tags and Go JSON
omission rules. No runtime source change was made for this failure.

The original test, runner, patch and `qualification/` logs are retained.
The second attempt uses `candidate-v2.patch`, the current `inputs/`, and
`qualification-v2/` in a fresh Linux output directory.

The first runner's parent namespace argument was empty, so its comparison
did not prove that the namespace differed from the parent. Its link inventory
did show only a down loopback device. Do not treat that initial comparison as
verified isolation. The second launcher obtains the parent namespace ID in
Python before `unshare`; the runner requires a nonempty namespace ID, compares
it with its own, and records the link inventory and unprivileged UID.

The initial `go env` was collected in the workspace, while the test command
ran in the selected node tree as recorded in its command metadata. The second
run records `go env` separately in each actual selected source directory.
