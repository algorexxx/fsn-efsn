# Observer byte-identity preflight refusal

At 08:30 UTC on 16 October, host checks passed but Linux preflight refused:
`ValueError: observer must change exactly one height literal` at
`preflight.py:28`, `inputs/replay_monitor.py:79`. No image attachment or writer
was started. This directory preserves every prepared file available at refusal,
including the old input manifest and host validation records.

The original observer was 3,779 bytes with no CRLF sequences; the prepared
observer was 3,881 bytes with 102 CRLF sequences. Windows text output changed
line endings as well as the endpoint literal. Correct the unlaunched inputs
using byte replacement, regenerate the exact byte diff and input seal, update
the runner's pinned input seal, and repeat host and Linux preflight. Do not
change the controller or weaken its byte-identity check.
