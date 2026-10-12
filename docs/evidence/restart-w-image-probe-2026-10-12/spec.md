# W-backed Linux image feasibility check

Direct DrvFs LevelDB creation failed with a directory fsync I/O error. Keep
that failed fixture. Test the identical binary first on a fresh local control,
then on a newly created 256 MiB raw image on W:, exposed through a dedicated
Linux loop device and formatted ext4. The image is an independent data disk;
do not move, mount or format an existing VHD, checkpoint or backup.

Verify the exact loop-device/backing-file identity before formatting only that
new disposable image. Keep mounts private, only loopback down in the process
network namespace, and no real blockchain input. Run the same 32 MiB synthetic
DB test. On success, unmount and run read-only e2fsck; detach the loop device.
Retain small outputs. Timeout each command at 180 seconds, outer 480 seconds,
with 5/10-second kill grace. Linux/D:/W: reserves remain 20/50/100 GiB.

This establishes feasibility only. It does not claim network-loss/power-loss
durability or historical replay throughput, and does not start migration.
