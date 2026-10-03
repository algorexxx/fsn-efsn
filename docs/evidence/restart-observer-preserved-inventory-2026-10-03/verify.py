import hashlib
import json
from pathlib import Path
import re

evidence = Path(__file__).resolve().parent
workspace = evidence.parents[2]
attempts = {
    "attempt-1": [15130080, 15130079, 15129953, 15129952, 15129056, 15120080, 15030080, 14000000, 1000000],
    "attempt-2": [15130078, 15130064, 15129954],
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


saved = {item["id"]: item["result"] for item in read_json(workspace / "docs/evidence/restart-2026-09-23/responses.json")}
owners = ["0x9fc4c40e50f902b9aa641b4a32ebaafa5c9386a1", "0xa3ce60d2dbf51afa0ab106df1c44a2e48853817a"]
rows = []
for attempt, heights in attempts.items():
    folder = evidence / attempt
    require((folder / "finished.txt").exists(), f"Incomplete run: {attempt}")
    require((folder / "build.txt").read_bytes() == b"", f"Build diagnostics: {attempt}")
    before = (folder / "source-before.json").read_bytes()
    require(before == (folder / "source-after.json").read_bytes(), f"Source metadata changed: {attempt}")
    require(before == (evidence / "attempt-1/source-before.json").read_bytes(), "Source metadata differs across runs")
    require(re.search(r"(?:^|,)ro(?:,|$)", (folder / "mount.txt").read_text().split()[-1]), "Source mount is not read-only")
    network = (folder / "network.txt").read_text().splitlines()
    require(len(network) == 1 and network[0].split()[:2] == ["lo", "DOWN"], "Unexpected network state")
    for line in (folder / "sources.sha256").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        actual = hashlib.sha256((workspace / name).read_bytes()).hexdigest()
        require(actual == expected, f"Source changed: {name}")
    for height in heights:
        require((folder / f"{height}-exit.txt").read_text().strip() == "0", f"Probe failed: {height}")
        log = (folder / f"{height}.txt").read_text()
        require("--- PASS: TestPreservedHistoricalInventory" in log and "FAIL" not in log, f"Probe did not pass: {height}")
        data = read_json(folder / f"{height}.json")
        require(int(data["Header"]["number"], 16) == height and data["BackupHead"] == saved[3]["hash"], "Unexpected identity")
        require(data["TicketCacheWasEmpty"], "First lookup used populated ticket cache")
        reads = data["Reads"]
        require([item["Wallet"] for item in reads] == owners + owners[:1], "Unexpected wallet order")
        require(reads[0]["Tickets"] == reads[2]["Tickets"] and reads[0]["Error"] == reads[2]["Error"], "Repeated lookup differs")
        available = not data["StateError"]
        if available:
            require(data["TicketBlobHash"] == data["Header"]["mixHash"] and data["TicketBlobBytes"] > 0, "Missing ticket commitment comparison")
            require(all(not read["Error"] for read in reads), "Available state has query error")
        else:
            require("missing trie node" in data["StateError"], "Unexpected unavailable-state cause")
            require(all(read["Error"] and read["Tickets"] is None for read in reads), "Missing state was treated as empty success")
        if height == int(saved[3]["number"], 16):
            expected_header = {key: saved[3][key] for key in data["Header"]}
            require(data["MatchedSavedHead"] and data["Header"] == expected_header, "Saved head differs")
            require(data["AllTickets"] == len(saved[7]), "Saved total differs")
            for read in reads:
                expected = {key: value for key, value in saved[7].items() if value["Owner"] == read["Wallet"]}
                require((read["Tickets"] or {}) == expected, "Saved wallet inventory differs")
        resources = (folder / f"{height}-resources.txt").read_text()
        rss = int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", resources).group(1))
        rows.append({
            "height": height,
            "available": available,
            "all_tickets": data["AllTickets"] if available else None,
            "backup_wallet_tickets": len(reads[0]["Tickets"] or {}) if available else None,
            "donation_wallet_tickets": len(reads[1]["Tickets"] or {}) if available else None,
            "first_read_ms": reads[0]["Duration"] / 1_000_000,
            "repeat_read_ms": reads[2]["Duration"] / 1_000_000,
            "first_read_allocated_bytes": reads[0]["AllocatedBytes"],
            "database_open_seconds": data["DatabaseOpen"] / 1_000_000_000,
            "process_peak_rss_kib": rss,
        })
result = {
    "source_metadata_unchanged": True,
    "source": read_json(evidence / "attempt-1/source-before.json"),
    "samples": sorted(rows, key=lambda item: item["height"], reverse=True),
    "limitations": [
        "existing Fusion API method with test-only explicit-height backend; no running node or RPC transport",
        "fresh process ticket cache; operating-system disk cache was not cleared",
        "API timings exclude database startup and JSON serialization",
        "allocation counters are process-wide; peak RSS covers the entire probe",
        "sampled state availability is not a retention guarantee",
        "metadata comparison is not a new full-file content hash scan",
    ],
}
(evidence / "checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
