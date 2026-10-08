# Encoder candidate attempt 1 — patch packaging failure

8 October 2026. Preparation completed, but the first git apply --check failed
with nine `dev/null: No such file or directory` messages. The generated Git
patch used /dev/null for additions but omitted the `new file mode 100644`
extended header. No patch was applied and no helper or runtime was built or
executed. This is a patch-generation failure, not an encoding result.

Retain the candidate inputs, specification, generated patch and command record
unchanged. The next fresh attempt adds the missing metadata only, changes its
result path and includes this manifest in the prior-evidence chain. Runtime
inputs and test expectations stay identical.

Follow-up: [attempt 2](../restart-ticket-encoder-candidate-v2-2026-10-08/README.md).
