import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

B = Path(__file__).resolve().parent
REPO = B.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(path, pin):
    assert sha(path) == pin
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split(None, 1)
        assert sha(path.parent / name) == digest, name
        entries[name] = digest
    return entries


r = read(B / "qualification/run.json")
assert r["completed"] and r["preservation_pass"] and "failure" not in r
inputs = manifest(B / "INPUT_SHA256SUMS", "1318b30a45b00d3b794f6b1fd4cf56248ce332e6c0734853fdcaacae43641123")
startup = manifest(B / "START_SHA256SUMS", "b447fd936ebcf6286fbdc4b463d5d3f2bd45e9cafa7c2f8d14b6a66f50c7966a")
assert r["input_sha256"] == inputs
assert all(sha(REPO / name) == digest for name, digest in r["fixture_input_sha256"].items())
for name in ["completion.json", "host-run.json", "worker.json", "source-unmount.json"]:
    assert read(B / name)["exit"] == 0, name
assert read(B / "completion.json")["verified_pass"]
acceptance = read(B / "acceptance.json")
assert acceptance["pass"] and not acceptance["selected_release_changed"] and not acceptance["real_keys_used"]
assert acceptance["protected_unchanged"] == read(B / "environment.json")["protected_before"]
cleanup = read(B / "cleanup.json")
assert cleanup["source_unmounted"] and cleanup["protected_metadata_unchanged"] and not cleanup["test_image_attached"]
assert read(B / "host-run.json")["protected_images_unchanged"]
assert all(v["pass"] for v in read(B / "host-image-comparison.json")["images"].values())
post = read(B / "post-state.json")
assert not post["busy_processes"] and not post["matching_mounts"] and not post["test_image_loops"]
assert post["investigation_owner_lock_available"] and not read(B / "host-post-state.json")["dispatch_pid_present"]
assert r["uid"] == 1000 and r["netns"] != r["parent_netns"]
assert [(x["ifname"], x["operstate"]) for x in r["interfaces"]] == [("lo", "DOWN")]
assert [c["name"] for c in r["commands"]] == ["command-build", "harness-build", "full-state-operator"]
for command, limit in zip(r["commands"], [1200, 900, 660]):
    assert command["exit"] == 0 and command["elapsed_seconds"] < limit
    assert command["argv"][:3] == ["timeout", "--kill-after=20s", str(limit) + "s"]
assert r["elapsed_seconds"] < 3300
expected = {name: digest for name, digest in read(B / "retained-source-inventory.json").items()
            if not name.startswith("tests/restart/")}
for path in (B / "harness").iterdir():
    expected["tests/restart/" + path.name] = sha(path)
context = "docs/evidence/restart-full-state-2026-09-24/context.rlp"
expected[context] = sha(REPO / context)
assert r["build_source_inventory"] == expected
assert r["go_binary_sha256"] == "30969f97169d7f43fe6a085873d75613adc21e30818a8c61d95bd27275df4624"
assert all(r["go_env"][k] == v for k, v in {
    "GOVERSION": "go1.27.1", "GOOS": "linux", "GOARCH": "amd64", "GOAMD64": "v1",
    "CGO_ENABLED": "1", "GOPROXY": "off", "GOSUMDB": "off", "GOTOOLCHAIN": "local",
    "GOFLAGS": "-mod=readonly"}.items())
assert r["copies"]["files_each"] == 230 and r["copies"]["bytes_each"] == 528817080 and r["copies"]["copies"] == 3
compact = {}
for line in (REPO / "docs/evidence/restart-state-export-2026-09-24/artifact-SHA256SUMS").read_text().splitlines():
    digest, name = line.split(None, 1)
    compact[name.removeprefix("./")] = digest
assert r["copies"]["source_hashes"] == compact
legacy = read(B.parent / "restart-full-state-operator-2026-09-25/identities.json")
comparisons = {}
for name, digest in legacy["prior_byte_identical_reference_artifacts"].items():
    relative = name.split("/artifacts/", 1)[1]
    assert sha(REPO / name) == digest == sha(B / "qualification/artifacts" / relative)
    comparisons[relative] = digest
assert len(comparisons) == 11 and r["legacy_reference_artifacts_match"] == comparisons
artifacts = B / "qualification/artifacts"
files = [p for p in artifacts.rglob("*") if p.is_file()]
assert len(r["closed_fixture_hashes"]) == 764
for path in files:
    assert sha(path) == r["closed_fixture_hashes"][path.relative_to(artifacts).as_posix()]
for stage, quota in [(1, 1), (2, 2), (3, 2)]:
    approval = read(artifacts / f"operator-{stage}-approval.json")
    report = read(artifacts / f"operator-{stage}-report.json")
    assert approval["Policy"]["BlockCount"] == quota
    assert approval["Policy"]["ExecutableSHA256"] == "0x" + r["binary_sha256"]["fsn-recovery"]
    assert approval["Plan"] == report["Plan"] == read(artifacts / f"operator-{stage}-plan.json")
    assert approval["UnsignedBlock"] == report["UnsignedBlock"]
    assert bytes.fromhex(approval["Purchase"].removeprefix("0x")) == (artifacts / f"operator-{stage}-purchase.rlp").read_bytes()
    expected_rlp = (artifacts / f"block-{stage:02}.rlp").read_bytes()
    assert (artifacts / f"operator-{stage}-block.rlp").read_bytes() == expected_rlp
    assert (artifacts / f"operator-{stage}-after-import.rlp").read_bytes() == expected_rlp
stdout = (B / "qualification/full-state-operator.stdout.txt").read_text()
assert "--- PASS: TestFullStateRecoveryOperator (" in stdout and stdout.endswith("PASS\n")
assert "--- SKIP:" not in stdout and "WARNING: DATA RACE" not in stdout and "panic:" not in stdout
for path in (B / "qualification").glob("*.stderr.txt"):
    assert not path.read_bytes(), path.name
for stage in [1, 2, 3]:
    assert f"stage={stage}: actual review/prepare/init/sign/export commands;" in stdout
assert "all future FSN rights conserved owner-by-owner" in stdout
samples = [json.loads(line) for line in (B / "qualification/resources.jsonl").read_text().splitlines()]
assert len(samples) == 15
floors = {"/home/rehearsal": 20, "/mnt/d": 50, "/mnt/c": 40}
min_free = {path: min(s["free_bytes"][path] for s in samples) for path in floors}
assert all(min_free[path] > floor * 2**30 for path, floor in floors.items())
maximum = max(s["run_logical_bytes"] for s in samples)
assert maximum < 12 * 2**30
result = dict(checked=datetime.now(timezone.utc).isoformat(), passed=True,
              scope="Independent record and archived-artifact review; no live database or image content read.",
              input_files=len(inputs), startup_files=len(startup), legacy_reference_artifacts=11,
              archived_artifacts=len(files), closed_fixture_hashes=764, resource_samples=len(samples),
              minimum_sampled_free_bytes=min_free, maximum_sampled_run_logical_bytes=maximum,
              elapsed_monotonic_seconds=r["elapsed_seconds"],
              elapsed_wall_seconds=(datetime.fromisoformat(r["finished"]) - datetime.fromisoformat(r["started"])).total_seconds(),
              image_metadata_comparison="Original supplemental false comparison retained; typed UTC ticks and length match.",
              selected_release_changed=False, independent_human_review_complete=False)
(B / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
