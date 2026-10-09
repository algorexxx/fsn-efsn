# Archival attempt refused before copying

9 October 2026. The mount-identity assertion refused execution: /mnt/w
resolved to the Linux root filesystem instead of the verified W: mount.
A subsequent findmnt confirmed that W: was no longer mounted. The earlier
mount had been verified, but its disappearance was not diagnosed further.

The assertion runs before checkpoint locks, creation of the archive directory,
copying or local deletion. No checkpoint was changed by this attempt. Preserve
the script, command result, stderr and failure record unchanged.

The [corrected launcher](../restart-checkpoint-archive-w-v2-2026-10-09/spec.md)
mounts W: in its own mount namespace and keeps the launcher alive throughout
the operation. That is an explicit new attempt with separate logs.
