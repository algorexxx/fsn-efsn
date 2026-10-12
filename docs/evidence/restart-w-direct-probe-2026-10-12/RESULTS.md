# Preflight-only refusal

The first attempt exited before creating runtime output, compiling, opening a
database or writing W: data. Its check read `/sys/class/net` inherited from the
parent mount namespace; that is not a reliable interface inventory for the new
network namespace. Retain the failed attempt. The corrected v2 probe queries
`ip -j link show` inside the new network namespace and requires only loopback,
without the UP flag. This result says nothing about W: database compatibility.
