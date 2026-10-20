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


def manifest(name, pin):
    path = B / name
    assert sha(path) == pin
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(None, 1)
        assert sha(B / relative) == digest, relative
        entries[relative] = digest
    return entries


r = read(B / "qualification/run.json")
assert r["completed"] and r["preservation_pass"] and "failure" not in r
inputs = manifest("INPUT_SHA256SUMS", "2ac3c26fd149ae74acbf2a324358e128828c285a2483a97a2d44fbb298f7bee1")
startup = manifest("START_SHA256SUMS", "064ee49ef9670b7b8f2da33ad73627ad16463f33b5f7bc1ba9d6cf138d598b9f")
assert r["input_sha256"] == inputs
assert r["completed_operator_files_verified"] == 109 and r["prior_files_verified"] == 139
for name in ["completion.json", "host-run.json", "worker.json", "source-unmount.json"]:
    assert read(B / name)["exit"] == 0, name
assert read(B / "completion.json")["verified_pass"]
acceptance = read(B / "acceptance.json")
assert acceptance["pass"] and not acceptance["selected_release_changed"] and not acceptance["real_keys_used"]
assert acceptance["protected_unchanged"] == read(B / "environment.json")["protected_before"]
cleanup = read(B / "cleanup.json")
assert cleanup["source_unmounted"] and cleanup["protected_metadata_unchanged"] and not cleanup["test_image_attached"]
assert read(B / "host-run.json")["protected_images_unchanged"]
post = read(B / "post-state.json")
assert not post["busy_processes"] and not post["matching_mounts"] and not post["test_image_loops"]
assert post["investigation_owner_lock_available"]
host = read(B / "host-post-state.json")
assert not host["dispatch_pid_present"] and all(v["pass"] for v in host["images"].values())
assert r["uid"] == 1000 and r["netns"] != r["parent_netns"]
assert [(x["ifname"], x["operstate"]) for x in r["interfaces"]] == [("lo", "DOWN")]
assert [c["name"] for c in r["commands"]] == ["harness-build", "approved-cuts"]
for command, limit in zip(r["commands"], [900, 960]):
    assert command["exit"] == 0 and command["elapsed_seconds"] < limit
    assert command["argv"][:3] == ["timeout", "--kill-after=20s", str(limit) + "s"]
assert r["elapsed_seconds"] < 2100
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
    "CGO_ENABLED": "1", "GOPROXY": "off", "GOSUMDB": "off",
    "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly"}.items())
stdout = (B / "qualification/approved-cuts.stdout.txt").read_text()
for test in ["ApprovedOfflineProcessCuts", "ApprovedOfflineRefusals", "KeystorePreflightLocksAndUncertain"]:
    assert "--- PASS: Test" + test + " (" in stdout
assert stdout.endswith("PASS\n") and "--- SKIP:" not in stdout and "WARNING: DATA RACE" not in stdout
assert "panic:" not in stdout and "--- FAIL:" not in stdout
for path in (B / "qualification").glob("*.stderr.txt"):
    assert not path.read_bytes(), path.name
for cut in ["completion", "export", "import"]:
    for stage in [1, 2, 3]:
        assert f"approved stage={stage} cut={cut}: exact recovery without another callback; independent cold ledgers agree" in stdout
for cut in ["reservation", "signature"]:
    assert f"kill-after={cut}: repeat signing and export refused; chain bytes unchanged" in stdout
for case in ["policy_quota", "policy_parent", "policy_executable", "policy_config",
             "purchase_owner", "parent", "purchase_bytes", "unsigned_bytes"]:
    assert "--- PASS: TestApprovedOfflineRefusals/" + case + " (" in stdout
assert "credential validation holds both locks; wrong password permits a later attempt; unfinished signature refuses key access" in stdout
artifacts = B / "qualification/artifacts"
files = [p for p in artifacts.rglob("*") if p.is_file()]
for path in files:
    assert sha(path) == r["closed_fixture_hashes"][path.relative_to(artifacts).as_posix()]
assert sorted(p.name for p in artifacts.iterdir()) == r["retained_cases"] and len(r["retained_cases"]) == 7
recovered = []
step_reference = None
for case in artifacts.iterdir():
    steps = [read(case / f"step-{i}.json") for i in [1, 2, 3]]
    expected_blocks = [s["Expected"] for s in steps]
    if step_reference is None:
        step_reference = expected_blocks
    assert expected_blocks == step_reference
    if any(f"ProcessCuts_{cut}-" in case.name for cut in ["completion", "export", "import"]):
        for stage, step in enumerate(steps, 1):
            path = case / f"recovered-{stage}.rlp"
            assert path.read_bytes() == bytes.fromhex(step["Expected"].removeprefix("0x"))
            exported = case / f"export-{stage}.rlp"
            if exported.exists():
                assert exported.read_bytes() == path.read_bytes()
            recovered.append(path.relative_to(artifacts).as_posix())
    else:
        assert not list(case.glob("recovered-*.rlp")) and not list(case.glob("export-*.rlp"))
assert len(recovered) == 9
samples = [json.loads(line) for line in (B / "qualification/resources.jsonl").read_text().splitlines()]
floors = {"/home/rehearsal": 20, "/mnt/d": 50, "/mnt/c": 40}
minimum = {path: min(s["free_bytes"][path] for s in samples) for path in floors}
assert all(minimum[path] > floor * 2**30 for path, floor in floors.items())
maximum = max(s["run_logical_bytes"] for s in samples)
assert maximum < 4 * 2**30
result = dict(checked=datetime.now(timezone.utc).isoformat(), passed=True,
              scope="Independent records and archived artifacts; no live database or image hashing.",
              input_files=len(inputs), startup_files=len(startup), tests=3, cut_subtests=5,
              changed_approval_subtests=8, exact_recovered_artifacts=recovered,
              uncertain_refusals=2, retained_cases=r["retained_cases"],
              archived_artifacts=len(files), closed_fixture_hashes=len(r["closed_fixture_hashes"]),
              resource_samples=len(samples), minimum_sampled_free_bytes=minimum,
              maximum_sampled_run_logical_bytes=maximum,
              elapsed_monotonic_seconds=r["elapsed_seconds"],
              elapsed_wall_seconds=(datetime.fromisoformat(r["finished"]) - datetime.fromisoformat(r["started"])).total_seconds(),
              selected_release_changed=False, independent_human_review_complete=False)
(B / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
