# Retained harness failure

The build and synthetic seeder both exited zero. The runner then refused the
seed stdout because `%s` rendered `common.Hash` as raw bytes, not UTF-8.
No CLI command ran. This is not a candidate startup result. Retain raw logs and
fixture bytes. A fresh v2 changes only this test log to `child.Hash().Hex()`.
Runtime source, CLI and release selection are unchanged.
