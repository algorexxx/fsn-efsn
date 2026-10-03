import hashlib
import json
import re
import statistics
from pathlib import Path

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
attempt = evidence / "attempt-1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


for line in (attempt / "sources.sha256").read_text(encoding="utf-8").splitlines():
    digest, name = line.split(maxsplit=1)
    require(hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest, f"Source changed: {name}")
network = (attempt / "network.txt").read_text(encoding="utf-8").splitlines()
require(len(network) == 1 and network[0].split()[0] == "lo", "Unexpected interface")
summary = {}
for mode in ["plain", "race"]:
    run = attempt / mode
    root = run / "workload"
    require((run / "test-exit.txt").read_text(encoding="utf-8").strip() == "0", f"Failed test: {mode}")
    log = (run / "tests.txt").read_text(encoding="utf-8")
    require("--- PASS: TestObserverMixedWorkloadBudget" in log and "FAIL" not in log and "DATA RACE" not in log, f"Unclean test: {mode}")
    require(log.count("--- PASS: TestRestartNodeRehearsal") == 2, "Missing clean node exits")
    require(all((run / name).read_bytes() == b"" for name in ["build-tests.txt", "build-observer.txt"]), "Build diagnostics")
    result = read(root / "result.json")
    require(result["Passed"] and result["OrdinaryMining"] and not result["RuntimeChanges"] and not result["LargeBackupRead"] and result["PublicTestKeys"] == [1, 2], "Unexpected scope")
    require(result["Rounds"] == 6 and result["BudgetBytes"] == 524288 and 0 < result["LogicalBytes"] < result["BudgetBytes"], "Unexpected bounds")
    config = read(root / "ipc-config.json")
    truth = read(root / "anchor-truth.json")
    ledger = read(root / "final-ledger.json")
    require(ledger["Header"] == result["Final"], "Final state/head mismatch")
    anchor = (root / "anchor-export.json").read_bytes()
    settled = (root / "settled-export.json").read_bytes()
    before = (root / "before-retry-export.json").read_bytes()
    final = (root / "offline-export.json").read_bytes()
    require(settled.startswith(anchor) and final.startswith(settled) and final == before, "Evidence changed or was pruned")
    events = [json.loads(line) for line in final.splitlines()][1:]
    require([event["Sequence"] for event in events] == list(range(1, len(events) + 1)), "History sequence is discontinuous")
    offline = read(root / "offline-status.json")
    require(offline == read(root / "backfill-rejected-status.json") and offline["Sequence"] == len(events) and offline["LogicalBytes"] == result["LogicalBytes"], "Rejection or offline opening changed persisted status")
    for i, node in enumerate(config["Nodes"]):
        baseline = read(root / f'{node["Name"]}-anchor.json')
        require(baseline["Status"] == "ready" and baseline["Tickets"] == truth[i]["Tickets"], "Anchor baseline differs from independent state")
        timeline = read(root / f'{node["Name"]}-offline-timeline.json')
        expected = {key: value for key, value in ledger["Tickets"].items() if value["Owner"] == node["Wallet"]}
        require(timeline["Status"] == "complete_for_retained_prefix" and timeline["Through"]["Hash"] == result["Final"]["hash"] and timeline["Inventory"] == expected, "Offline inventory differs from executed state")
    commands = read(root / "commands.json")
    rejected = []
    stopped = 0
    groups = {}
    prior_heights = {node["Name"]: config["AnchorNumber"] for node in config["Nodes"]}
    last_status = None
    expected_rejection_status = None
    for command in commands:
        name = command["Name"]
        require(command["Nanoseconds"] > 0 and command == read(root / f"{name}-command.json"), "Invalid command measurement")
        diagnostics = (root / f"{name}-stderr.txt").read_text(encoding="utf-8")
        if command["ExitCode"] == 1:
            require((root / f"{name}.json").read_bytes() == b"" and diagnostics == "history byte budget exhausted; evidence retained without pruning\n", "Unexpected command failure")
            expected_rejection_status = last_status
            rejected.append(name)
        else:
            require(command["ExitCode"] == 0 and diagnostics == "", "Command diagnostics")
            if "export" not in name:
                payload = read(root / f"{name}.json")
                if name.endswith("rejected-status"):
                    require(payload == expected_rejection_status, "Rejected append changed its previous status")
                if "History" in payload:
                    last_status = payload["History"]
                elif "LogicalBytes" in payload:
                    last_status = payload
        if not command["Before"]:
            require(not command["After"] and name.startswith(("offline-", "node-")), "Unexpected command without running nodes")
        elif not any(node["Mining"] for node in command["Before"]):
            require(command["Before"] == command["After"], "Stopped node changed")
            stopped += 1
        else:
            producer = next(i for i, node in enumerate(config["Nodes"]) if node["Name"] == result["Producer"])
            for i, prior in enumerate(command["Before"]):
                after = command["After"][i]
                require(prior["Mining"] == after["Mining"] == prior["AutoBuy"] == after["AutoBuy"] == (i == producer) and after["Number"] >= prior["Number"], "Collection changed production controls")
        match = re.fullmatch(r"round-([1-6])-(ipc|http)-(snapshot|node-[12]-backfill)", name)
        if match:
            round_number, transport, operation = match.groups()
            require(transport == ("ipc" if int(round_number) % 2 else "http"), "Unexpected transport schedule")
            kind = "snapshot" if operation == "snapshot" else "backfill"
            groups.setdefault(f"{transport}_{kind}", []).append(command["Nanoseconds"] / 1e6)
            payload = read(root / f"{name}.json")
            if kind == "snapshot":
                require(len(payload["Nodes"]) == 2 and all(node["Consistency"] == "stable" and node["Identity"] == "matches" and node["TicketsKnown"] for node in payload["Nodes"]), "Unstable workload snapshot")
            else:
                node_name = operation.removesuffix("-backfill")
                coverage = next(item for item in payload["Blocks"] if item["Node"] == node_name)
                require(coverage["Status"] == "complete_at_observation" and coverage["StoredThrough"]["Number"] > prior_heights[node_name], "Block coverage did not advance")
                prior_heights[node_name] = coverage["StoredThrough"]["Number"]
    require("retry-snapshot" in rejected and "retry-backfill" in rejected and any(name.startswith("fill-snapshot-") for name in rejected) and any(name.startswith("fill-backfill-") for name in rejected), "Missing budget rejection cases")
    require(all(len(groups[f"{transport}_{kind}"]) == count for transport in ["ipc", "http"] for kind, count in [("snapshot", 3), ("backfill", 6)]), "Missing live command samples")
    summary[mode] = {"passed": True, "final_height": int(result["Final"]["number"], 16), "retained_events": len(events), "logical_bytes": result["LogicalBytes"], "budget_bytes": result["BudgetBytes"], "closed_file_bytes": result["ClosedFileBytes"], "rejected_commands": rejected, "unchanged_stopped_command_captures": stopped, "offline_inventories_match": True, "exports_preserved": True}
    if mode == "plain":
        summary[mode]["live_command_timings_ms"] = {name: {"samples": len(values), "min": min(values), "median": statistics.median(values), "max": max(values)} for name, values in groups.items()}
summary["limitations"] = ["compact six-round workload, three observations per transport", "local IPC and loopback HTTP without production network latency", "only 512 KiB logical history; long-term scaling remains open", "race-instrumented timings are not performance measurements", "no full filesystem, power-loss, retention migration or notification delivery test"]
(evidence / "checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
