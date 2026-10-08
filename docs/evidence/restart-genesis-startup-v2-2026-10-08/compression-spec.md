# Compression follow-up

The completed CLI runs reproduce the default-genesis mismatch on both
executables. The retained 23 September genesis response differs from the new
header in state root and ticket commitment. StateDB hashes the gzip-compressed
ticket RLP and stores those same compressed bytes in account code.

Bounded causal check: extract the synthetic default genesis's ticket RLP, feed
that identical input to gzip.NewWriter in the existing Go 1.21.3 and 1.27.1
toolchains, and compare compressed bytes and decompressed payloads. In a fresh
in-memory genesis only, substitute the old compiler's compressed bytes at the
ticket account and recompute the state root and header commitment. Compare the
entire resulting header to the retained historical response. No real database,
runtime patch or expected historical hash is changed.

Use fresh output paths, private namespace, cached compilers, two workers and
seven-minute build limits. Preserve all bytes, compiler/library hashes and
commands. A matching genesis identifies this input's cause; it does not prove
all historical ticket encodings or select a compression compatibility fix.
