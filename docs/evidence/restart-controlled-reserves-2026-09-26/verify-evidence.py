import hashlib
import json
import re
import subprocess
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]


def git(*args):
    return subprocess.check_output(["git", "-c", "core.safecrlf=false", *args], cwd=workspace).decode().strip()


def read(name):
    return (evidence / name).read_text(encoding="utf-8")


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


baseline = git("rev-parse", "ee0165f")
assert baseline in read("environment.txt") and "go version go1.21.3 linux/amd64" in read("environment.txt")
assert read("build.txt") == "" and int(read("controlled-initial-exit.txt")) == 0
assert read("binary.sha256").split()[0] == digest(workspace / "tmp/controlled-reserve-tests")
data = read("controlled-initial-race.txt")
assert "WARNING: DATA RACE" not in data and "--- SKIP:" not in data and "--- FAIL:" not in data
duration = re.findall(r"^--- PASS: TestRestartNodeRehearsal \(([0-9.]+)s\)", data, re.MULTILINE)
assert len(duration) == 1 and data.endswith("PASS\n")
assert "--- PASS: TestRestartNodeRehearsal/dense_miner_fixture" in data
assert "complete synthetic genesis-to-24 ancestry independently executed" in data
parent = re.search(r"controlled zero-ticket parent height=(\d+) hash=(0x[0-9a-f]+) state=(0x[0-9a-f]+) tickets=(0x[0-9a-f]+) affected=(0x[0-9a-fA-F]+) nonce=(\d+) liquid-wei=(\d+) locks=(\[.*\]);", data)
assert parent and len(re.findall(r"controlled prefix first-retreat=", data)) == 2
results = {"duration_seconds": float(duration[0]), "baseline": dict(zip(["height", "hash", "state_root", "ticket_root", "owner", "nonce", "liquid_wei", "locks"], parent.groups())), "cases": {}}
results["baseline"]["locks"] = json.loads(parent[8])
expected = {
    "no_funding": (0, 0, 2),
    "one_ticket_funding": (5000, 7, 2),
    "two_ticket_funding": (10000, 7, 2),
    "one_ticket_missed_again": (5000, 1, 3),
}
sequences = {}
for name, (funding, count, losses) in expected.items():
    marker = "=== RUN   TestRestartNodeRehearsal/controlled_zero_ticket_reserves/" + name + "\n"
    section = data.split(marker, 1)[1].split("=== RUN   TestRestartNodeRehearsal/controlled_zero_ticket_reserves/", 1)[0]
    assert "--- PASS: TestRestartNodeRehearsal/controlled_zero_ticket_reserves/" + name + " (" in data
    row = re.search(r"controlled result case=(\w+) baseline=(0x[0-9a-f]+) topup-wei=(\d+) included=(\d+) funding-wait-blocks=(\d+) final=(\d+) hash=(0x[0-9a-f]+) state=(0x[0-9a-f]+) tickets=(0x[0-9a-f]+)", section)
    assert row and row[1] == name and row[2] == parent[2]
    assert int(row[3]) == funding * 10**18 and int(row[4]) == count
    final = int(row[6])
    purchases = re.findall(r"controlled original nonce=(\d+) hash=(0x[0-9a-f]+) included=(\d+) block=(0x[0-9a-f]+)", section)
    assert len(purchases) == count and [int(tx[0]) for tx in purchases] == list(range(int(parent[6]), int(parent[6]) + count))
    sequences[name] = [(tx[0], tx[1]) for tx in purchases]
    waits = re.findall(r"controlled admission nonce=(\d+) hash=(0x[0-9a-f]+) waited-blocks=(\d+)", section)
    assert [(tx[0], tx[1]) for tx in waits] == sequences[name]
    assert sum(int(tx[2]) for tx in waits) == int(row[5])
    cold = re.findall(r"controlled cold node=(\d+) purchases=(\d+) sponsor-nonce=(\d+) sponsor-liquid-wei=(\d+) head=(0x[0-9a-f]+)", section)
    balance = (11000 - funding) * 10**18 - (21000 * 10**9 if funding else 0)
    assert cold == [(str(i), str(count), str(int(funding != 0)), str(balance), row[7]) for i in [1, 2]]
    audits = re.findall(r"ledger verified phase=controlled range=(\d+)\.\.(\d+) head=(0x[0-9a-f]+)", section)
    assert audits == [("25", str(final), row[7])]
    blocks = [int(value) for value in re.findall(r"ledger block phase=controlled height=(\d+)", section)]
    assert blocks == list(range(25, final + 1))
    retreats = re.findall(r"ledger retreat phase=controlled block=(\d+) hash=(0x[0-9a-f]+) index=0 owner=(0x[0-9a-fA-F]+) ticket=(0x[0-9a-f]+) start=(\d+) end=(\d+) value-wei=5000000000000000000000 returned=false", section)
    assert len(retreats) == losses and all(tx[2] == parent[5] and int(tx[5]) - int(tx[4]) == 30*24*3600 for tx in retreats)
    assert f"owner={parent[5]} first-retreats={losses}" in section
    if name == "no_funding":
        assert "twelve canonical blocks advanced; zero tickets and no repair admitted" in section
    if name == "one_ticket_missed_again":
        assert f"next nonce={int(parent[6]) + 1} remains unfunded" in section
    results["cases"][name] = {
        "topup_wei": row[3], "included": count, "wait_blocks": [int(tx[2]) for tx in waits],
        "final": dict(zip(["height", "hash", "state_root", "ticket_root"], row.groups()[5:])),
        "purchases": purchases, "first_retreats": retreats, "cold_nodes": 2, "sponsor_end_wei": str(balance),
    }
assert sequences["one_ticket_funding"] == sequences["two_ticket_funding"]
assert sequences["one_ticket_missed_again"] == sequences["one_ticket_funding"][:1]

changed = git("diff", "--name-only", baseline).splitlines()
assert not [name for name in changed if (name.endswith(".go") and not name.endswith("_test.go")) or name in ["go.mod", "go.sum"]]
names = [
    "tests/restart/controlled_reserve_fixture_linux_test.go", "tests/restart/controlled_reserve_linux_test.go",
    "tests/restart/dense_miner_fixture_linux_test.go", "tests/restart/node_rehearsal_linux_test.go",
    "tests/restart/partition_funds_ledger_linux_test.go", "tests/restart/full_state_handover_ledger_test.go",
    "tests/restart/full_state_handover_fixture_test.go", "tests/restart/blocks_test.go",
    "tests/restart/fixture_test.go", "tests/restart/competing_miners_linux_test.go",
    "consensus/datong/consensus.go", "core/state_transition.go", "core/state/statedb.go",
    "core/tx_pool.go", "common/fsnargs.go", "common/timelock.go", "common/ticket.go",
    "internal/ethapi/autobuy.go", "internal/ethapi/api_fsn.go", "go.mod", "go.sum",
    "docs/evidence/restart-full-state-handover-2026-09-24/windows-handover.json",
]
donation = json.loads((workspace / names[-1]).read_text(encoding="utf-8"))
assert donation["Donation"] == "0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a"
assert donation["Liquid"] == "12020102000000000000000" and donation["Nonce"] == 0
identities = {"baseline": baseline, "runtime_changed": False, "sources": {name: {"git_blob": git("hash-object", "--path=" + name, name), "sha256": digest(workspace / name)} for name in names}}
for name, content in [("results.json", results), ("identities.json", identities)]:
    (evidence / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8", newline="\n")
files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(evidence / "SHA256SUMS").write_text("".join(f"{digest(path)}  {path.name}\n" for path in files), encoding="utf-8", newline="\n")
print(f"Verified four controlled cases, eight cold nodes, four interval ledgers, {len(names)} source identities and {len(files)} evidence hashes; no production source/dependency changes")
