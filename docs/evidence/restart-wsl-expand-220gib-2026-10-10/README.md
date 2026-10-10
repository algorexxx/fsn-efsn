# Authorized FusionRehearsal disk expansion

Peter explicitly approved the proposed 200 to 220 GiB expansion on 10 October:
"question somehow went away bet yes, feel free to expand it".

Only FusionRehearsal's disk is resized. The first distro-only stop left its VHD
attached; native resize refused before mutation. After confirming Docker had no
running containers and no other distro was running, `finish-resize.py` briefly
stops the idle Docker backend, shuts down WSL, performs the approved expansion,
and restarts Docker. All logs, including the first refusal, remain preserved.
Native `wsl --manage` receives the exact 236,223,201,280-byte target.
Microsoft's [size syntax](https://learn.microsoft.com/en-us/windows/wsl/disk-space)
supports integer bytes. The current [WSL implementation](https://github.com/microsoft/WSL/blob/master/src/windows/service/exe/LxssUserSession.cpp)
refuses an attached target disk before resizing and operates on that distro's
VHD. Installed behavior and actual
post-operation geometry are authoritative for this run.

`check.py before` validates the sealed 5,600,032 checkpoint evidence, idle
processes, actual database/run locks, protected metadata, replay identity,
source/binary/toolchain/STOP and capacity. `check.py after` additionally verifies
all working and recovery file hashes against the sealed inventories. Both use
private mount/network namespaces, loopback DOWN, read-only views and a ten-minute
external deadline. The backup is checked by metadata, not newly hashed in full.

The native resize is one invocation, with its process/logs retained if it takes
longer than a tool call. Do not interrupt filesystem resizing merely because a
tool yields. Any failure holds further mutation and replay pending diagnosis.
No repair, compaction, cleanup, network contact from tests, real keys or release
change is authorized by this operation. Keep the 20/50 GiB Linux/D: reserves.
