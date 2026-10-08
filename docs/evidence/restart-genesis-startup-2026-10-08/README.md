# Retained startup probe fixture failure

8 October 2026. The baseline helper built and its in-memory construction ran.
The first actual node command exited 1 before genesis initialization: an explicit
empty --bootnodesv4= argument was parsed as an invalid enode. The candidate and
restart/reader cases did not execute. This is a fixture configuration failure,
not evidence of a genesis or restored-datadir refusal.

The profile already specifies empty bootstrap arrays, and discovery/peers are
disabled in the private namespace. The follow-up removes the redundant empty
bootstrap CLI arguments and uses a fresh directory. Runtime files, executable
hashes and observation expectations are unchanged. See the sibling
restart-genesis-startup-v2-2026-10-08 bundle. Original logs are preserved.
