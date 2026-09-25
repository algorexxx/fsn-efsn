import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import snapshot_package as snapshot


class SnapshotPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        for name, data in {"CURRENT": b"MANIFEST-000001\n", "MANIFEST-000001": b"manifest", "000001.ldb": b"public-chain-data" * 20, "LOCK": b""}.items():
            (self.source / name).write_bytes(data)
        self.identity = {"head": "synthetic", "chain_id": 32659}
        self.package = self.root / "package"
        self.silent = contextlib.redirect_stdout(io.StringIO())
        self.silent.__enter__()
        self.addCleanup(self.silent.__exit__, None, None, None)

    def pack(self, **kwargs):
        return snapshot.pack(self.source, self.package, self.identity, 32, 0, **kwargs)

    def test_complete_roundtrip_and_reused_target(self):
        self.pack()
        manifest = snapshot.digest(self.package / "manifest.json")
        target = self.root / "restored"
        snapshot.restore(self.package, target, manifest, 0)
        actual = {path.name: path.read_bytes() for path in (target / "chaindata").iterdir()}
        expected = {path.name: path.read_bytes() for path in self.source.iterdir()}
        self.assertEqual(expected, actual)
        with self.assertRaises(FileExistsError):
            snapshot.restore(self.package, target, manifest, 0)

    def test_bounded_resume_keeps_completed_archive(self):
        self.assertIsNone(self.pack(max_parts=1))
        archive = self.package / "part-00000.zip"
        before = (archive.stat().st_mtime_ns, archive.read_bytes())
        self.assertFalse((self.package / "manifest.json").exists())
        self.pack(resume=True)
        self.assertEqual(before, (archive.stat().st_mtime_ns, archive.read_bytes()))

    def test_changed_source_and_identity_refuse_resume(self):
        self.pack(max_parts=1)
        self.identity["chain_id"] = 1
        with self.assertRaisesRegex(ValueError, "changed"):
            self.pack(resume=True)
        self.identity["chain_id"] = 32659
        (self.source / "CURRENT").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.pack(resume=True)

    def test_tampered_completed_archive_refuses_resume(self):
        self.pack(max_parts=1)
        (self.package / "part-00000.zip").write_bytes(b"broken")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.pack(resume=True)

    def test_changed_completed_source_with_same_metadata_refuses_resume(self):
        self.pack(max_parts=1)
        path = self.source / "000001.ldb"
        before = path.stat()
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError, "completed source checksum"):
            self.pack(resume=True)

    def test_separate_process_package_lock_excludes_writer(self):
        self.package.mkdir()
        code = "from pathlib import Path; import sys; import snapshot_package as s\nwith s.package_lock(Path(sys.argv[1])):\n print('locked', flush=True)\n sys.stdin.readline()\n"
        child = subprocess.Popen([sys.executable, "-c", code, str(self.package)],
                                 cwd=Path(snapshot.__file__).parent, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual("locked\n", child.stdout.readline())
            with self.assertRaises(OSError):
                with snapshot.package_lock(self.package):
                    self.fail("concurrent package lock succeeded")
        finally:
            _, errors = child.communicate("release\n", timeout=10)
        self.assertEqual(0, child.returncode, errors)
        with snapshot.package_lock(self.package):
            pass

    def test_partial_archive_is_never_a_complete_package(self):
        with patch.object(snapshot, "pack_part", side_effect=OSError("simulated network disconnect")):
            with self.assertRaises(OSError):
                self.pack()
        self.assertFalse((self.package / "manifest.json").exists())
        (self.package / "part-00000.zip.interrupted.partial").write_bytes(b"partial")
        self.pack(resume=True)
        snapshot.load_package(self.package, snapshot.digest(self.package / "manifest.json"))

    def test_key_and_directory_entries_refused(self):
        (self.source / "nodekey").write_bytes(b"synthetic-forbidden-file")
        with self.assertRaisesRegex(ValueError, "approved"):
            snapshot.inventory(self.source)
        (self.source / "nodekey").unlink()
        (self.source / "keystore").mkdir()
        with self.assertRaisesRegex(ValueError, "approved"):
            snapshot.inventory(self.source)

    def test_orphan_archive_revalidated_before_resume(self):
        self.pack(max_parts=1)
        archive = self.package / "part-00000.zip"
        original = archive.read_bytes()
        (self.package / "part-00000.json").unlink()
        self.pack(resume=True)
        self.assertEqual(original, archive.read_bytes())

    def test_trusted_manifest_and_corrupt_archive(self):
        self.pack()
        target = self.root / "restored"
        with self.assertRaisesRegex(ValueError, "trusted manifest"):
            snapshot.restore(self.package, target, "0" * 64, 0)
        self.assertFalse(target.exists())
        expected = snapshot.digest(self.package / "manifest.json")
        (self.package / "part-00000.zip").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "archive checksum"):
            snapshot.restore(self.package, target, expected, 0)
        self.assertFalse((target / "restored.json").exists())

    def test_final_output_readback_failure_prevents_completion_marker(self):
        self.pack()
        expected = snapshot.digest(self.package / "manifest.json")
        target = self.root / "restored"
        original_digest = snapshot.digest

        def changed_output(path):
            if path.parent == target / "chaindata" and path.name == "000001.ldb":
                return "0" * 64
            return original_digest(path)

        with patch.object(snapshot, "digest", side_effect=changed_output):
            with self.assertRaisesRegex(ValueError, "restored-file checksum"):
                snapshot.restore(self.package, target, expected, 0)
        self.assertTrue((target / "chaindata/000001.ldb").exists())
        self.assertFalse((target / "restored.json").exists())

    def test_traversal_and_duplicate_manifest_entries(self):
        self.pack()
        for name in ["../nodekey", "CURRENT"]:
            part_path = self.package / "part-00000.json"
            part = snapshot.read_json(part_path)
            part["files"][0]["name"] = name
            part_path.write_text(json.dumps(part), encoding="utf-8")
            manifest_path = self.package / "manifest.json"
            manifest = snapshot.read_json(manifest_path)
            manifest["parts"][0]["sha256"] = snapshot.digest(part_path)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid or duplicate"):
                snapshot.load_package(self.package, snapshot.digest(manifest_path))

    def test_reserve_and_stop_leave_no_completion_marker(self):
        with self.assertRaisesRegex(ValueError, "reserve"):
            snapshot.pack(self.source, self.package, self.identity, 32, 10**30)
        stop = self.root / "STOP"
        stop.touch()
        self.assertIsNone(self.pack(resume=True, stop=stop))
        self.assertFalse((self.package / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
