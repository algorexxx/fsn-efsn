"""Test-only, flat LevelDB snapshot packaging. The Go runner holds the source lock."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import time
import uuid
import zipfile


FILE_NAME = re.compile(r"(?:[0-9]+\.(?:ldb|sst|log)|MANIFEST-[0-9]+|CURRENT(?:\.bak)?|LOG(?:\.old)?|LOCK)\Z")
BLOCK = 4 * 1024 * 1024


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as reader:
        while data := reader.read(BLOCK):
            result.update(data)
    return result.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".partial")
    with temporary.open("xb") as writer:
        writer.write((json.dumps(value, sort_keys=True, indent=2) + "\n").encode())
        writer.flush()
        os.fsync(writer.fileno())
    if path.exists():
        raise ValueError(f"refusing existing metadata: {path}")
    temporary.rename(path)


@contextmanager
def package_lock(directory):
    with (directory / "writer.lock").open("a+b") as lock:
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def inventory(source):
    files = []
    for path in sorted(source.iterdir()):
        info = path.lstat()
        if not FILE_NAME.fullmatch(path.name) or not stat.S_ISREG(info.st_mode) or path.is_symlink():
            raise ValueError(f"not an approved flat LevelDB file: {path.name}")
        if getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("source reparse points are forbidden")
        files.append({"name": path.name, "size": info.st_size, "mtime_ns": info.st_mtime_ns})
    if "CURRENT" not in [entry["name"] for entry in files] or not any(entry["name"].startswith("MANIFEST-") for entry in files):
        raise ValueError("source lacks CURRENT or manifest")
    return files


def check_space(directory, needed, reserve):
    if shutil.disk_usage(directory).free < needed + reserve:
        raise ValueError("storage reserve reached")


def groups(files, maximum):
    current, size = [], 0
    for item in files:
        if current and size + item["size"] > maximum:
            yield current
            current, size = [], 0
        current.append(item)
        size += item["size"]
    if current:
        yield current


def pack_part(source, destination, number, files, reserve):
    name = f"part-{number:05d}.zip"
    final = destination / name
    if final.exists():
        entries = []
        with zipfile.ZipFile(final) as archive:
            if [member.filename for member in archive.infolist()] != [item["name"] for item in files]:
                raise ValueError("orphan archive differs from planned inventory")
            for item in files:
                member = archive.getinfo(item["name"])
                if member.file_size != item["size"] or member.compress_type != zipfile.ZIP_STORED:
                    raise ValueError("orphan archive file size or encoding differs")
                checksum = hashlib.sha256()
                with archive.open(member) as reader:
                    while data := reader.read(BLOCK):
                        checksum.update(data)
                if digest(source / item["name"]) != checksum.hexdigest():
                    raise ValueError("orphan archive content differs from source")
                entries.append({"name": item["name"], "size": item["size"], "sha256": checksum.hexdigest()})
        result = {"name": name, "size": final.stat().st_size, "sha256": digest(final), "files": entries}
        write_json(destination / f"part-{number:05d}.json", result)
        return result
    temporary = destination / (name + "." + uuid.uuid4().hex + ".partial")
    check_space(destination, sum(item["size"] for item in files) + len(files) * 256 + 1024, reserve)
    entries = []
    with temporary.open("xb") as output:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
            for item in files:
                path = source / item["name"]
                info = path.stat()
                if info.st_size != item["size"] or info.st_mtime_ns != item["mtime_ns"]:
                    raise ValueError("source changed before read")
                checksum, size = hashlib.sha256(), 0
                member = zipfile.ZipInfo(item["name"])
                member.external_attr = (stat.S_IFREG | 0o600) << 16
                with path.open("rb") as reader, archive.open(member, "w", force_zip64=True) as writer:
                    while data := reader.read(BLOCK):
                        writer.write(data)
                        checksum.update(data)
                        size += len(data)
                after = path.stat()
                if size != item["size"] or after.st_size != info.st_size or after.st_mtime_ns != info.st_mtime_ns:
                    raise ValueError("source changed during read")
                entries.append({"name": item["name"], "size": size, "sha256": checksum.hexdigest()})
        output.flush()
        os.fsync(output.fileno())
    if final.exists():
        raise ValueError(f"archive exists without committed metadata: {name}")
    temporary.rename(final)
    result = {"name": name, "size": final.stat().st_size, "sha256": digest(final), "files": entries}
    write_json(destination / f"part-{number:05d}.json", result)
    return result


def pack(source, destination, identity, maximum, reserve, resume=False, max_parts=None, stop=None):
    source, destination = source.resolve(), destination.resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError("source and package directories must be separate")
    if not resume:
        destination.mkdir()
    elif not destination.is_dir():
        raise ValueError("resume requires an existing package")
    with package_lock(destination):
        files = inventory(source)
        plan = {"format": 1, "kind": "fusion-flat-leveldb", "source": str(source), "identity": identity,
                "part_bytes": maximum, "files": files, "packer_sha256": digest(Path(__file__))}
        if resume:
            if read_json(destination / "source.json") != plan:
                raise ValueError("source inventory, identity, packer or layout changed")
        else:
            write_json(destination / "source.json", plan)
        completed, written, start = [], 0, time.monotonic()
        for number, batch in enumerate(groups(files, maximum)):
            metadata = destination / f"part-{number:05d}.json"
            if metadata.exists():
                part = read_json(metadata)
                if [(item["name"], item["size"]) for item in part["files"]] != [(item["name"], item["size"]) for item in batch]:
                    raise ValueError("completed part differs from planned inventory")
                if part["name"] != f"part-{number:05d}.zip" or digest(destination / part["name"]) != part["sha256"]:
                    raise ValueError("completed archive checksum mismatch")
                for item in part["files"]:
                    if digest(source / item["name"]) != item["sha256"]:
                        raise ValueError("completed source checksum mismatch")
            else:
                if (max_parts is not None and written >= max_parts) or (stop and stop.exists()):
                    print(json.dumps({"complete": False, "parts": len(completed), "seconds": time.monotonic() - start}), flush=True)
                    return None
                part = pack_part(source, destination, number, batch, reserve)
                written += 1
                print(json.dumps({"part": number, "bytes": part["size"], "seconds": round(time.monotonic() - start, 2)}), flush=True)
            completed.append({"name": metadata.name, "sha256": digest(metadata)})
        if inventory(source) != files:
            raise ValueError("source inventory changed during packaging")
        result = {"format": 1, "kind": "fusion-flat-leveldb", "identity": identity,
                  "source_plan_sha256": digest(destination / "source.json"), "parts": completed,
                  "files": len(files), "bytes": sum(item["size"] for item in files)}
        final = destination / "manifest.json"
        if final.exists():
            if read_json(final) != result:
                raise ValueError("existing final manifest differs")
        else:
            write_json(final, result)
        print(json.dumps({"complete": True, "manifest_sha256": digest(final), "parts": len(completed), "bytes": result["bytes"]}), flush=True)
        return result


def load_package(package, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or digest(package / "manifest.json") != expected:
        raise ValueError("trusted manifest checksum mismatch")
    manifest = read_json(package / "manifest.json")
    if manifest["format"] != 1 or manifest["kind"] != "fusion-flat-leveldb":
        raise ValueError("unsupported package format")
    if digest(package / "source.json") != manifest["source_plan_sha256"]:
        raise ValueError("source plan checksum mismatch")
    parts, names, size = [], set(), 0
    for number, reference in enumerate(manifest["parts"]):
        if reference["name"] != f"part-{number:05d}.json" or digest(package / reference["name"]) != reference["sha256"]:
            raise ValueError("part metadata checksum or sequence mismatch")
        part = read_json(package / reference["name"])
        if part["name"] != f"part-{number:05d}.zip":
            raise ValueError("invalid part archive path")
        for item in part["files"]:
            name = item["name"]
            if not FILE_NAME.fullmatch(name) or name.casefold() in names or not isinstance(item["size"], int) or item["size"] < 0 or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                raise ValueError("invalid or duplicate database file entry")
            names.add(name.casefold())
            size += item["size"]
        parts.append(part)
    if len(names) != manifest["files"] or size != manifest["bytes"] or "current" not in names or not any(name.startswith("manifest-") for name in names):
        raise ValueError("package inventory totals or mandatory files differ")
    return manifest, parts


def restore(package, destination, expected, reserve, stop=None):
    package, destination = package.resolve(), destination.resolve()
    manifest, parts = load_package(package, expected)
    if destination == package or package in destination.parents or destination in package.parents:
        raise ValueError("package and restore directories must be separate")
    check_space(destination.parent, manifest["bytes"] + len(parts) * 4096, reserve)
    destination.mkdir()
    database = destination / "chaindata"
    database.mkdir()
    start = time.monotonic()
    for number, part in enumerate(parts):
        if stop and stop.exists():
            raise ValueError("restore stopped; incomplete target cannot be started")
        path = package / part["name"]
        if path.stat().st_size != part["size"] or digest(path) != part["sha256"]:
            raise ValueError("archive checksum mismatch")
        check_space(destination, sum(item["size"] for item in part["files"]), reserve)
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if [item.filename for item in members] != [item["name"] for item in part["files"]]:
                raise ValueError("archive entries differ from manifest")
            for member, expected_file in zip(members, part["files"]):
                if member.file_size != expected_file["size"] or member.compress_type != zipfile.ZIP_STORED or member.is_dir() or stat.S_ISLNK(member.external_attr >> 16):
                    raise ValueError("unsupported archive member")
                checksum, size = hashlib.sha256(), 0
                with archive.open(member) as reader, (database / member.filename).open("xb") as writer:
                    while data := reader.read(BLOCK):
                        size += len(data)
                        if size > expected_file["size"]:
                            raise ValueError("archive member exceeds declared size")
                        writer.write(data)
                        checksum.update(data)
                if size != expected_file["size"] or checksum.hexdigest() != expected_file["sha256"]:
                    raise ValueError("restored file checksum mismatch")
        print(json.dumps({"restored_part": number, "seconds": round(time.monotonic() - start, 2)}), flush=True)
    for part in parts:
        for item in part["files"]:
            if digest(database / item["name"]) != item["sha256"]:
                raise ValueError("cold restored-file checksum mismatch")
    if len(inventory(database)) != manifest["files"]:
        raise ValueError("restored database inventory differs")
    write_json(destination / "restored.json", {"manifest_sha256": expected, "files": manifest["files"], "bytes": manifest["bytes"], "identity": manifest["identity"]})
    print(json.dumps({"restored": True, "files": manifest["files"], "bytes": manifest["bytes"]}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["pack", "restore"])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--part-bytes", type=int, default=512 * 1024**2)
    parser.add_argument("--reserve-bytes", type=int, default=100 * 1024**3)
    parser.add_argument("--max-parts", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop", type=Path)
    args = parser.parse_args()
    if not args.source.is_absolute() or not args.destination.is_absolute() or args.part_bytes <= 0 or args.reserve_bytes < 0 or (args.max_parts is not None and args.max_parts < 0):
        parser.error("absolute paths and nonnegative limits required")
    if args.mode == "pack":
        if not args.identity:
            parser.error("pack requires source identity and the Go runner's held read-only database lock")
        pack(args.source, args.destination, read_json(args.identity), args.part_bytes, args.reserve_bytes, args.resume, args.max_parts, args.stop)
    else:
        restore(args.source, args.destination, args.manifest_sha256 or "", args.reserve_bytes, args.stop)


if __name__ == "__main__":
    main()
