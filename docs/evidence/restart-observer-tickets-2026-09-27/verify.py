import hashlib
import json
import re
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
attempt = evidence / "attempt-1"
fixture = workspace / "docs/evidence/restart-observer-mining-2026-09-27/attempt-3/mining"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


for name, expected in read_json(evidence / "inputs.sha256.json").items():
    require(digest(workspace / name) == expected, f"Input changed: {name}")
sources = read_json(attempt / "windows/sources.json")
for name, expected in sources.items():
    require(digest(workspace / name) == expected, f"Source changed: {name}")
linux_sources = {}
for line in (attempt / "linux/sources.sha256").read_text(encoding="utf-8").splitlines():
    expected, name = line.split(maxsplit=1)
    linux_sources[name] = expected
require(sources == linux_sources, "Platform source manifests differ")

tests = {}
for platform in ["windows", "linux"]:
    folder = attempt / platform
    output = (folder / "tests.txt").read_text(encoding="utf-8")
    require((folder / "test-exit.txt").read_text().strip() == "0", f"{platform} test exit failed")
    require("FAIL" not in output and "DATA RACE" not in output, f"{platform} test failure")
    for package in ["internal/observe", "cmd/fsn-observe"]:
        require(re.search(r"^ok\s+github.com/FusionFoundation/efsn/v5/" + re.escape(package) + r"\s", output, re.M), f"Missing {platform} package")
    require((folder / "build.txt").read_bytes() == b"", f"{platform} compiler output")
    tests[platform] = {"passes_including_subtests": len(re.findall(r"^\s*--- PASS:", output, re.M)), "race_detection": platform == "linux", "log_sha256": digest(folder / "tests.txt")}
network = (attempt / "linux/network.txt").read_text().splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected network interface")
require(len({tests[p]["passes_including_subtests"] for p in tests}) == 1, "Platform test counts differ")

ledger = read_json(fixture / "ledger-29.json")["Tickets"]
native = read_json(fixture / "native-events.json")
wallets = {}
for name, count, event_count in [("node-1", 11, 2), ("node-2", 12, 9)]:
    windows, linux = attempt / "windows" / (name + ".json"), attempt / "linux" / (name + ".json")
    require(windows.read_bytes() == linux.read_bytes(), f"Platform timeline differs: {name}")
    timeline = read_json(windows)
    owner = timeline["Wallet"]
    expected_inventory = {key: value for key, value in ledger.items() if value["Owner"] == owner}
    expected_events = [entry for entry in native if entry["Ticket"]["Owner"] == owner]
    require(timeline["Status"] == "complete_for_retained_prefix" and timeline["BaselineSequence"] == 1 and timeline["Sequence"] == 10, f"Wrong timeline provenance: {name}")
    require(timeline["Through"] == {"Number": 29, "Hash": "0x7ac9a79e964f18731c9182fd1a40565d540fe4b40f897dae5d975da8bb79598d"}, f"Wrong final block: {name}")
    require(timeline["Inventory"] == expected_inventory and len(expected_inventory) == count, f"Inventory differs: {name}")
    require(len(timeline["Events"]) == len(expected_events) == event_count, f"Event count differs: {name}")
    for actual, expected in zip(timeline["Events"], expected_events):
        require(actual["Block"] == {"Number": expected["Height"], "Hash": expected["Block"]}, f"Event block differs: {name}")
        for key in ["Kind", "TicketID", "Ticket"]:
            require(actual[key] == expected[key], f"Event {key} differs: {name}")
        if expected["Kind"] == "purchase":
            require(actual["Transaction"] == expected["Transaction"], "Purchase binding differs")
        if expected["Kind"] == "retreat":
            require(actual["RetreatIndex"] == 0 and actual["Return"] == "none_first_retreat", "Retreat attribution differs")
        if expected["Kind"] == "selection":
            require(actual["Return"] == "interval_rights", "Selection attribution differs")
    wallets[name] = {"inventory": count, "events": event_count, "timeline_sha256": digest(windows)}

result = {"tests": tests, "wallets": wallets, "source_files": len(sources), "scope": "offline retained rehearsal and synthetic observer unit tests; no fresh node execution or production-state claim"}
(evidence / "checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
