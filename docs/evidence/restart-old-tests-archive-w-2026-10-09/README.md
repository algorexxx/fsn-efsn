# Initial archival attempt — refused before copying

The directory-parent validation used PowerShell PSIsContainer adaptation on
a raw DirectoryInfo parent. Strict mode rejected it before any fixture was
copied, hashed or removed. The only W: change was the empty destination root.
Original script, console output and failure record are retained.

Continue with the [corrected v2 operation](../restart-old-tests-archive-w-v2-2026-10-09/README.md), which uses a new destination.
