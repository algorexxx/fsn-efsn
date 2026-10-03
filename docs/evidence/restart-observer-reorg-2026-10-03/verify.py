import hashlib
import json
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
run = evidence / "attempt-3"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


for line in (run / "sources.sha256").read_text().splitlines():
    expected, name = line.split(maxsplit=1)
    require(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == expected, f"Source changed: {name}")
for name in ["build-tests.txt", "build-observer.txt"]:
    require((run / name).read_bytes() == b"", f"Build diagnostics: {name}")
network = (run / "network.txt").read_text().splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected network interface")
for attempt, failure in [("attempt-1", "both ordinary miners must have signed"), ("attempt-2", "partition ledger requires known owners and no remaining genesis tickets")]:
    folder = evidence / attempt
    require((folder / "reorg-exit.txt").read_text().strip() == "1" and failure in (folder / "reorg-race.txt").read_text(encoding="utf-8"), f"Missing retained test assumption failure: {attempt}")
    manifest = {name: digest for digest, name in (line.split(maxsplit=1) for line in (folder / "sources.sha256").read_text().splitlines())}
    for source in folder.glob("*_test.go"):
        require(hashlib.sha256(source.read_bytes()).hexdigest() == manifest[f"tests/restart/{source.name}"], f"Failed-attempt source differs: {source.name}")
for mode, test in [("reorg", "TestObserverCompetingReorganization"), ("ordinary", "TestObserverOrdinaryMining")]:
    require((run / f"{mode}-exit.txt").read_text().strip() == "0", f"{mode} failed")
    log = (run / f"{mode}-race.txt").read_text(encoding="utf-8")
    require(f"--- PASS: {test}" in log and "FAIL" not in log and "DATA RACE" not in log, f"{mode} did not pass cleanly")
    require(log.count("--- PASS: TestRestartNodeRehearsal") == 4, f"Missing clean child exits: {mode}")
    result = read_json(run / mode / "result.json")
    require(result["Passed"] and result["OrdinaryMining"] and not result["HeldSigner"] and not result["ControlledDownloader"] and not result["LargeBackupRead"], f"Unexpected test scope: {mode}")

root = run / "reorg"
result = read_json(root / "result.json")
require(not result["RuntimeChanges"], "Unexpected runtime changes")
loser = result["Loser"]
index = int(loser.split("-")[1]) - 1
config = read_json(root / "ipc-config.json")
truth = read_json(root / "anchor-truth.json")
ledger = read_json(root / "final-ledger.json")
require(ledger["Header"] == result["Final"], "Final ledger/head differ")
before = read_json(root / "before-connect.json")
require(all(node["Mining"] and node["AutoBuy"] for node in before), "Both miners were not active before joining")
isolated = read_json(root / "isolated-first-blocks.json")
require(isolated[0]["hash"] != isolated[1]["hash"], "Isolated branches do not differ")
for i, block in enumerate(isolated):
    require(block["parentHash"] == result["Anchor"]["hash"] and block["miner"] == config["Nodes"][i]["Wallet"], "Isolated block does not belong to its ordinary producer")
cases = {}
for mode in ["snapshot", "backfill"]:
    folder = root / mode
    window = read_json(folder / "window.json")
    allowed = {"web3_clientVersion", "net_version", "eth_chainId", "eth_getBlockByNumber", "eth_syncing", "eth_mining", "fsn_isAutoBuyTicket", "eth_coinbase", "net_peerCount", "eth_getTransactionCount", "fsn_getBalance", "fsn_getRawTimeLockBalance", "fsn_allTicketsByAddress", "txpool_content", "eth_getTransactionReceipt", "eth_getRawTransactionByBlockHashAndIndex"}
    require(set(window["Methods"]) <= allowed, "Proxy saw a method outside the read allowlist")
    replacement = read_json(folder / "replacement-at-pinned-height.json")
    require(window["Completed"] and not window["Error"], f"Incomplete read gate: {mode}")
    require(int(replacement["number"], 16) == window["PinnedHeight"] and replacement["hash"] != window["PinnedHash"], f"No observed branch change: {mode}")
    original = (folder / "before-export.json").read_bytes()
    during = (folder / "during-export.json").read_bytes()
    final = (folder / "final-export.json").read_bytes()
    require(during.startswith(original) and final.startswith(during), f"Original evidence rewritten: {mode}")
    events = [json.loads(line) for line in during.splitlines()]
    final_events = [json.loads(line) for line in final.splitlines()]
    if mode == "snapshot":
        report = read_json(folder / "during-reorg.json")
        observed = report["Nodes"][index]
        require(observed["Head"]["Hash"] == window["PinnedHash"] and observed["Consistency"] == "changed_or_unavailable", "Cross-branch snapshot not invalidated")
        require(len(observed["Tracked"]) == 1, "Missing tracked purchase")
        require(all(observed["Tracked"][0][field] == "unknown" for field in ["Inclusion", "Funding", "Payload", "NonceRelation"]), "Cross-branch purchase classification remained authoritative")
    else:
        backfill = events[-1]["Backfill"]
        require(backfill["Status"] == "unstable" and backfill["Base"] is None and not backfill["Blocks"], "Unstable backfill retained candidate branch data")
        prior = read_json(folder / f"{loser}-isolated.json")
        actual = read_json(folder / "during-reorg.json")
        old_coverage = next(block for block in prior["Blocks"] if block["Node"] == loser)
        new_coverage = next(block for block in actual["Blocks"] if block["Node"] == loser)
        require(old_coverage["StoredThrough"] == new_coverage["StoredThrough"] and new_coverage["Status"] == "unstable", "Unstable acquisition moved retained coverage")
    for i, node in enumerate(config["Nodes"]):
        inventory = read_json(folder / f'{node["Name"]}-anchor.json')
        require(inventory["Status"] == "ready" and inventory["Tickets"] == truth[i]["Tickets"], "Pre-launch baseline differs from independent state")
        timeline = read_json(folder / f'{node["Name"]}-final-timeline.json')
        cold = read_json(folder / f'{node["Name"]}-cold-timeline.json')
        expected = {key: value for key, value in ledger["Tickets"].items() if value["Owner"] == node["Wallet"]}
        coverage = read_json(folder / f'{node["Name"]}-final-backfill.json')
        require(timeline["Sequence"] == coverage["Sequence"] and cold["Sequence"] == final_events[-1]["Sequence"], "Timeline does not identify its history version")
        require({key: value for key, value in timeline.items() if key != "Sequence"} == {key: value for key, value in cold.items() if key != "Sequence"}, "Cold wallet timeline changed")
        require(timeline["Status"] == "complete_for_retained_prefix" and timeline["Through"]["Hash"] == result["Final"]["hash"] and timeline["Inventory"] == expected, "Derived final inventory differs from executed state")
    status = read_json(folder / "node-2-final-backfill.json")
    require(any(item["Kind"] == "canonical_history_change" and item["Node"] == loser and item["Status"] == "open" for item in status["Incidents"]), "Canonical change incident was hidden or resolved")
    unchanged = 0
    for path in folder.glob("*-state.json"):
        capture = read_json(path)
        require(capture["Before"] == capture["After"], f"Stopped-node state changed: {path.name}")
        unchanged += 1
    for path in folder.glob("*-command.json"):
        capture = read_json(path)
        require(all(item["Mining"] and item["AutoBuy"] for item in capture["Before"]), "Command did not start during mining")
        require(all(item["AutoBuy"] for item in capture["After"]), "Command changed automatic buying")
    for path in folder.glob("*-stderr.txt"):
        require(path.read_bytes() == b"", f"Observer command diagnostics: {path.name}")
    cases[mode] = {"pinned_height": window["PinnedHeight"], "old_hash": window["PinnedHash"], "replacement_hash": replacement["hash"], "unchanged_stopped_node_captures": unchanged, "original_evidence_retained": True, "both_final_and_cold_inventories_match": True}

summary = {"passed": True, "linux_race_detection": True, "displaced_node": loser, "final_height": int(result["Final"]["number"], 16), "cases": cases, "ordinary_mining_regression": True, "limitations": ["one compact synthetic branch replacement", "staggered starts and test-induced RPC delays", "ordinary initial peer join, not a public outage/reconnect", "no claim of both buyers replenishing after reorganization", "no production backlog/storage or notification-delivery validation"]}
(evidence / "checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
