# Historical ticket DEFLATE writer

Unselected F12 compatibility candidate. The five writer files are unchanged
copies from Go 1.21.3 src/compress/flate, covered by the included Go BSD license.
shared.go contains its maxNumLit constant and InternalError definition/method,
extracted from inflate.go. No decompressor is included.

Keep this implementation private to ticketgzip. Ticket commitments depend on
exact encoded bytes, so an encoder update requires historical-byte qualification
and consensus review. The package is intentionally not a general compression
replacement. Mechanical upstream provenance and retained golden vectors are
part of the review input; do not silently regenerate them with this encoder.
