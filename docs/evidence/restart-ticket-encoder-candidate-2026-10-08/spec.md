# F12 encoder-only candidate qualification

Prepare an unselected patch against frozen P1–P17+B1+D1 node and recovery
sources. Copy five writer files byte-for-byte from the pinned Go 1.21.3
installation, preserve its license, and extract only maxNumLit and InternalError
from inflate.go. Add a ticket-only Encode function with the fixed default gzip
envelope; integrate it only in calcTicketsStorageData. Do not copy a decoder,
alter GOROOT, dependencies, ticket rules, fork settings or activation heights.

Use fresh disposable source copies, no backup/datadir access, no real keys,
offline dependencies and a private network namespace (only loopback DOWN).
Check >30 GiB Linux and >60 GiB D: free. Build/probe limits are seven/two minutes;
actual CLI invocations 45 seconds. Preserve failed attempts without overwriting.

Three modes: unchanged selected source with Go 1.21.3 (differential comparator),
unchanged selected source with Go 1.27.1 (control), and the candidate with Go
1.27.1. All helper builds use race detection. Fixed tests are:

1. Seven historical vectors from the preceding immutable evidence. Require
   initially empty ticket cache for each hash, then load the saved bytes through
   AllTickets (the real decoder), update without expiry at timestamp zero,
   and check full RLP, compressed bytes, MixDigest and AddCachedTickets. Compare
   the entire constructed default genesis header to the preserved header.
   The synthetic state contains only the ticket account: its root is compared
   between modes, never called a historical block-root oracle.
2. Fifty-five synthetic byte inputs: empty once; lengths 1, 2, 255, 256, 257,
   258, 259, 16383, 16384, 16385, 32767, 32768, 32769, 65534, 65535, 65536,
   65537 and 131072 with zeros, a repeated structured string, and a deterministic
   SHA-256 counter stream. Require candidate output identical to the old
   encoder, repeated and four concurrent calls identical, Python gzip decode
   exact, fixed 10-byte header and independent CRC32/ISIZE trailer checks.
   Empty gzip is independently specified by an empty final DEFLATE stored block
   and zero CRC/length, rather than copied from observed candidate output.
3. Six expiry cases: owner A tickets 1/2 expire at 100/101; owner B ticket 3
   expires at 200 (all start at zero, height one). Timestamps 99, 100, 101, 199,
   200, 201 must retain IDs [1,2,3], [2,3], [3], [3], [1,2,3], [1,2,3]. Last
   two return the existing no-surviving-ticket error and write no ticket blob.
   Independently construct expected survivor RLP in Python, verify ordering and
   fields, and compare candidate compression/roots to the old-mode results.
4. Build actual candidate efsn and fsn-recovery. Start and restart only the
   synthetic empty CLI datadir using the already retained disabled-mining,
   disabled-purchase, zero-peer profile. Compare its genesis header, heads and
   configuration using the existing read-only inspector, with before/after file
   hashes unchanged. Capture the recovery help command; do not sign anything.

Passing means the candidate agrees with these independent historical/format/
survivor expectations and the stated differential comparisons. Modern control
differences are retained, not made passing by changing expectations. Seven
sampled blobs do not prove missing historical states or whole-history execution.
Full affected regressions, cost measurement, candidate historical replay,
independent consensus/maintenance review and restore-identity refusal remain
open. No final source selection or production activation follows this test.
