# Evidence packaging

The first staged whitespace check reported:

    qualification/helpers_test.go:79: new blank line at EOF.

The helper is the exact file used for compilation, including the separator
after its final extracted body. Preserve those bytes and recorded hashes.
Its local whitespace attribute permits that final blank line and the original
CRLF bodies. No experimental input, expectation or output was edited for this
packaging correction. The final SHA256SUMS includes the corrected attribute.
