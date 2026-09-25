from pathlib import Path
import sys

workspace = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(workspace / "tests/restart"))
import snapshot_package

package = Path("W:/FusionRestart/restore-rehearsal-2026-09-24/package")
assert (package / "writer.lock").is_file()
try:
    with snapshot_package.package_lock(package):
        raise AssertionError("second writer acquired the active SMB package lock")
except OSError as error:
    print(f"PASS: second process refused active SMB package lock: {error}", flush=True)
