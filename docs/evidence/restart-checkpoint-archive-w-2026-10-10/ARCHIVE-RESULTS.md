# Two superseded checkpoints archived

The finite archive phase completed on 10 October 2026 at 10:52:40 UTC with
exit 0. Both checkpoints (2,000,000 and 2,200,000) match their original sealed
cold SHA256 inventories after full copy, flush, archive readback and source
re-verification: 2,161 files, 4,874,392,642 logical bytes total.

The independent record/provenance verifier passes. Working/recovery metadata
and all other replay root names stayed unchanged while their locks were held.
At copy completion Linux had 23,321,100,288 bytes free, D: 68,254,081,024 bytes,
and W: 3,837,027,627,008 bytes. These are copy-stage observations. Both local
checkpoint directories are still present at this stage; no space was reclaimed
inside Linux. The separate authorized retirement must recheck all source and
archive bytes before removing only those two directories.

The W: destination is FusionRestart/checkpoint-archive-2026-10-10. archive.json
contains exact source/archive mappings, original file metadata and full hashes.
Old manifests retain their historical paths and meaning. Original backup,
current working state, recovery, failed runs and evidence remain preserved.
