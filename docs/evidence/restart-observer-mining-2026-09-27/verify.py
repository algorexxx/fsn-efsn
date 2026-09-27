import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
attempt = evidence / "attempt-3"
mining = attempt / "mining"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


baseline = (attempt / "baseline.txt").read_text(encoding="utf-8").strip()
sources = {}
unchanged_observer = []
for line in (attempt / "sources.sha256").read_text(encoding="utf-8").splitlines():
    expected, path = line.split(maxsplit=1)
    require(digest(workspace / path) == expected, f"Tested source changed: {path}")
    sources[path] = expected
    if path.startswith(("cmd/fsn-observe/", "internal/observe/")):
        original = subprocess.run(["git", "show", f"{baseline}:{path}"], cwd=workspace, check=True, capture_output=True).stdout
        require(hashlib.sha256(original).hexdigest() == expected, f"Observer source differs from baseline: {path}")
        unchanged_observer.append(path)

require((attempt / "exit.txt").read_text(encoding="utf-8").strip() == "0", "Mining test failed")
log = (attempt / "mining-race.txt").read_text(encoding="utf-8")
require("--- PASS: TestObserverOrdinaryMining" in log and "FAIL" not in log and "DATA RACE" not in log, "Missing race-test success")
require(log.count("--- PASS: TestRestartNodeRehearsal") == 4, "Missing clean initial/cold child exits")
require("partition ledger verified phase=observer-ordinary-mining" in log, "Missing interval-rights audit")
for name in ["build-tests.txt", "build-observer.txt"]:
    require((attempt / name).read_bytes() == b"", f"Compiler output: {name}")
network = (attempt / "network.txt").read_text(encoding="utf-8").splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected network surface")

result = read_json(mining / "result.json")
require(result["Passed"] and result["OrdinaryMining"] and result["PublicTestKeys"] == [1, 2], "Wrong mining scenario")
require(not any(result[key] for key in ["ControlledDownloader", "HeldSigner", "LargeBackupRead", "NodeRuntimeChanges"]), "Unexpected test scope")
anchor, final = result["Anchor"], result["Final"]
first, last = int(anchor["number"], 16), int(final["number"], 16)
require(first == 24 and last >= 29, "Insufficient ordinary progress")
producer = result["Producer"]
commands = sorted(mining.glob("*-command.json"))
require(len(commands) == 13, "Missing observer command records")
for path in commands:
    command = read_json(path)
    require(command["StartedUTC"] < command["FinishedUTC"], f"Bad command window: {path.name}")
    for i, (before, after) in enumerate(zip(command["Before"], command["After"])):
        active = command["MiningExpected"] and i == command["ProducerIndex"]
        require(all(state[key] == active for state in [before, after] for key in ["Mining", "AutoBuy"]), f"Control flags changed: {path.name}")
        require(after["Number"] >= before["Number"] and after["Signatures"] >= before["Signatures"], f"Progress went backward: {path.name}")
        require(i == command["ProducerIndex"] or after["Signatures"] == 0, f"Verifier signed: {path.name}")
    require(path.with_name(path.name.replace("-command.json", "-stderr.txt")).read_bytes() == b"", f"Observer stderr: {path.name}")


def coverage(name, node):
    return next(item for item in read_json(mining / (name + ".json"))["Blocks"] if item["Node"] == node)


partial = coverage("ipc-partial", producer)
require(partial["Status"] == "batch_limit" and partial["StoredThrough"]["Number"] == 25, "Wrong bounded starting prefix")
allowed = {"web3_clientVersion", "net_version", "eth_chainId", "eth_getBlockByNumber", "eth_syncing", "eth_mining", "fsn_isAutoBuyTicket", "eth_coinbase", "net_peerCount", "eth_getTransactionCount", "fsn_getBalance", "fsn_getRawTimeLockBalance", "fsn_allTicketsByAddress", "txpool_content", "eth_getTransactionReceipt", "eth_getRawTransactionByBlockHashAndIndex"}
windows = {}
for mode, method in [("snapshot", "eth_getTransactionCount"), ("backfill", "eth_getBlockByNumber")]:
    window = read_json(mining / ("moving-" + mode + "-window.json"))
    require(window["Completed"] and not window["Error"] and window["AdvancedHeight"] > window["PinnedHeight"], f"No natural head advance: {mode}")
    require(window["GateMethod"] == method and set(window["Methods"]) <= allowed, f"Unexpected proxy calls: {mode}")
    command = read_json(mining / ("moving-" + mode + "-command.json"))
    index = command["ProducerIndex"]
    require(command["Before"][index]["Number"] <= window["PinnedHeight"] < window["AdvancedHeight"] <= command["After"][index]["Number"], f"Advance outside command: {mode}")
    windows[mode] = {"pinned": window["PinnedHeight"], "advanced": window["AdvancedHeight"]}
snapshot = next(node for node in read_json(mining / "moving-snapshot.json")["Nodes"] if node["Name"] == producer)
require(int(snapshot["Head"]["Header"]["number"], 16) == windows["snapshot"]["pinned"] and snapshot["Consistency"] == "stable" and snapshot["Identity"] == "matches" and snapshot["TicketsKnown"] and not snapshot["Issues"], "Historical snapshot changed with head advance")
moving = coverage("moving-backfill", producer)
require(moving["Status"] == "batch_limit" and moving["StoredThrough"]["Number"] == 27 and moving["ObservedHead"]["Number"] == windows["backfill"]["pinned"], "Moving batch lost its pinned target")
for i in [1, 2]:
    require(coverage(f"live-catchup-{i}", f"node-{i}")["Status"] == "complete_at_observation", "Live catch-up incomplete")
    for phase in ["final-catchup", "cold-recheck"]:
        item = coverage(f"{phase}-{i}", f"node-{i}")
        require(item["Status"] == "complete_at_observation" and item["StoredThrough"] == item["ObservedHead"] == {"Number": last, "Hash": final["hash"]}, f"Final/cold coverage mismatch: {phase} {i}")

export = (mining / "history-export.jsonl").read_bytes()
cold_export = (mining / "cold-history-export.jsonl").read_bytes()
require(cold_export.startswith(export), "Cold export lost earlier evidence")
records = [json.loads(line) for line in export.splitlines()]
cold_records = [json.loads(line) for line in cold_export.splitlines()]
require("Metadata" in records[0] and len(records) == 9 and len(cold_records) == 11, "Unexpected event counts")
require([item["Sequence"] for item in cold_records[1:]] == list(range(1, 11)), "Export sequence gap")
require(b'"Endpoint"' not in cold_export, "Endpoint persisted in history")
retained = {"node-1": {}, "node-2": {}}
for record in cold_records[1:]:
    batch = record.get("Backfill")
    if not batch:
        continue
    for height, block in enumerate(batch.get("Blocks") or [], batch["Base"]["Number"] + 1):
        require(height not in retained[batch["Node"]], "Duplicate unforked fetch")
        retained[batch["Node"]][height] = block
require(retained["node-1"] == retained["node-2"] and set(retained["node-1"]) == set(range(first + 1, last + 1)), "Both-node history differs or has gaps")
native = read_json(mining / "native-events.json")
counts = Counter(item["Kind"] for item in native)
inventory = {}
for node in read_json(mining / "anchor-snapshot.json")["Nodes"]:
    require(node["Head"]["Hash"] == anchor["hash"] and node["TicketsKnown"], "Missing anchor inventory")
    inventory.update(node["Tickets"])
require(len(inventory) == result["Counts"]["anchor_tickets"], "Anchor count differs")
for height in range(first + 1, last + 1):
    block, ledger = retained["node-1"][height], read_json(mining / f"ledger-{height}.json")
    require(bytes.fromhex(block["RLP"][2:]) == (mining / f"block-{height}.rlp").read_bytes() and block["Receipts"] == ledger["Receipts"], f"Block/receipt artifact differs: {height}")
    for event in [item for item in native if item["Height"] == height]:
        require(event["Block"] == ledger["Header"]["hash"], f"Native event bound to wrong block: {height}")
        ticket_id = event["TicketID"]
        if event["Kind"] == "purchase":
            require(ticket_id not in inventory, "Duplicate ticket purchase")
            inventory[ticket_id] = event["Ticket"]
        else:
            require(inventory.pop(ticket_id) == event["Ticket"], "Removed ticket lacks matching ownership")
    require(inventory == ledger["Tickets"], f"Inventory replay differs at {height}")
require(result["Counts"] == {"anchor_tickets": 26, "blocks": last - first, "purchases": counts["purchase"], "selections": counts["selection"], "retreats": counts["retreat"], "expired": counts["expiry"], "final_tickets": len(inventory)}, "Counts differ from evidence")
require(counts["purchase"] >= 3 and counts["selection"] == last - first and counts["retreat"] > 0, "Missing required native outcomes")
require(any(item["Kind"] == "block_coverage" and item["Status"] == "open" for item in read_json(mining / "cold-recheck-2.json")["Incidents"]), "Catching up automatically resolved the incident")

binaries = {}
for line in (attempt / "binaries.sha256").read_text(encoding="utf-8").splitlines():
    expected, path = line.split(maxsplit=1)
    if (workspace / path).exists():
        require(digest(workspace / path) == expected, f"Binary changed: {path}")
        binaries[path] = expected
checks = {
    "baseline": baseline,
    "attempt": attempt.name,
    "sources_verified": len(sources),
    "observer_source_files_unchanged_from_baseline": len(unchanged_observer),
    "test": "TestObserverOrdinaryMining passed with race detection; four clean service exits; loopback only",
    "log_sha256": digest(attempt / "mining-race.txt"),
    "observer_commands": len(commands),
    "natural_head_advances": windows,
    "range": [first + 1, last],
    "final_hash": final["hash"],
    "native_counts": result["Counts"],
    "export_events_before_cold_recheck": len(records) - 1,
    "export_events_after_cold_recheck": len(cold_records) - 1,
    "both_nodes_and_replayed_inventory_agree": True,
    "built_binaries_present": binaries,
    "limitations": ["One ordinary producer and one verifier on compact synthetic history, not live reorganization or representative workload.", "Native reconstruction is test-only, with a known two-owner anchor inventory and successful purchase-only transactions.", "No real funding, keys, backup access, notification delivery or production deployment."],
}
(evidence / "checks.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
print(json.dumps(checks, indent=2))
