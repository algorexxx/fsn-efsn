# Retire two superseded historical checkpoints after W: verification

Authorized by Peter on 10 October 2026: "If there is something not needed any more you can delete it."

Only candidate-ticket-encoding-2000000 and candidate-ticket-encoding-2200000
under /home/rehearsal/replay are eligible. Copy to the new W: checkpoint-archive-2026-10-10
folder, verify against both sealed checkpoint inventories and unchanged source
bytes, then run a separate retirement phase that rechecks both complete copies.
The original backup, current 5,331,360 working DB, separate 2,400,000-v2 recovery,
earlier stopped attempt, all baselines, source/binaries and sealed evidence stay.
Working/recovery locks and metadata plus other root names are checked each phase.
Private mount/network namespaces; loopback DOWN; no node execution or contact.
W: is the authorized archival filesystem. Two-hour limit per phase, 20s kill grace.
Linux/D:/W: reserves remain 20/50/100 GiB. No VHD compaction. Preserve partial failures.
Restoration uses each archive.json source/archive mapping, full SHA256 inventory
and original per-file mode/mtime record; never run LevelDB on the network share.
