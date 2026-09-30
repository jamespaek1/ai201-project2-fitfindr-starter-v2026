#!/usr/bin/env python3
"""Collect raw, uncached evidence for the five original criteria.

The original runner handled only whole-agent queries. This version also runs
criterion 4's direct fit-card call and criterion 5's five distinct search cases.
It does not change the agent or decide subjective factual-grounding verdicts.
"""
import argparse
from contextlib import redirect_stdout, redirect_stderr
import datetime as dt
import hashlib
import io
import json
import subprocess
import time
import traceback

import config
import generate
import scenarios
import trace


def run_once(scenario, attempt):
    from agent import run_agent
    from mcp_client import call_tool
    from tools import create_fit_card
    from utils.data_loader import get_example_wardrobe, load_listings

    record = {"started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "attempt": attempt, "session": None, "output": None,
              "inputs": None, "error": None, "crashed": None}
    calls = generate.call_count()
    tokens = generate.token_counts()
    started = time.monotonic()
    capture = io.StringIO()
    with redirect_stdout(capture), redirect_stderr(capture):
        trace.start_trace()
        try:
            if scenario["kind"] == "agent":
                record["inputs"] = {"query": scenario["query"], "wardrobe": get_example_wardrobe()}
                record["session"] = run_agent(**record["inputs"])
                record["error"] = record["session"]["error"]
            elif scenario["kind"] == "fit_card":
                item = next(x for x in load_listings() if x["id"] == scenario["item_id"])
                record["inputs"] = {"outfit": scenario["outfit"], "new_item": item}
                record["output"] = create_fit_card(**record["inputs"])
                trace.step("create_fit_card (direct criterion 4)", inputs=record["inputs"],
                           returned=record["output"], full=True)
            else:
                case = scenario["cases"][(attempt - 1) % len(scenario["cases"])]
                record["inputs"] = {k: v for k, v in case.items() if k != "expected"}
                record["expected_id"] = case["expected"]
                record["output"] = call_tool("search_listings", record["inputs"])
                trace.step("search_listings (via MCP; criterion 5)", inputs=record["inputs"],
                           returned=record["output"], full=True)
        except Exception as exc:
            record["crashed"] = f"{type(exc).__name__}: {exc}"
            record["traceback"] = traceback.format_exc()
        record["trace"] = trace.get_trace()
    record["console"] = capture.getvalue()
    record["model_calls"] = generate.call_count() - calls
    record["tokens"] = {k: v - tokens[k] for k, v in generate.token_counts().items()}
    record["duration_seconds"] = round(time.monotonic() - started, 3)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--tries", type=int, default=5)
    args = parser.parse_args()
    if args.tries != 5:
        parser.error("These original criteria specify exactly five tries/cases.")
    if scenarios.validate():
        parser.error("; ".join(scenarios.validate()))
    config.CACHE_ENABLED = False
    if not args.label.replace("_", "").replace("-", "").isalnum():
        parser.error("Use a simple label, such as before or after.")
    path = config.RESULTS_DIR / f"unit4_{args.label}.json"
    if path.exists():
        parser.error(f"Refusing to overwrite prior evidence: {path.name}")
    source_files = ["criteria.md", "agent.py", "tools.py", "config.py", "generate.py",
                    "mcp_server.py", "mcp_client.py", "scenarios.py", "run_eval.py", "trace.py"]
    report = {
        "label": args.label, "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {p: hashlib.sha256((config.ROOT / p).read_bytes()).hexdigest() for p in source_files},
        "model": config.MODEL, "temperature": config.TEMPERATURE, "cache_enabled": False,
        "tries": 5, "criterion_5_note": "Five original distinct cases, once each in their original order.",
        "rows": [],
    }
    config.RESULTS_DIR.mkdir(exist_ok=True)
    print(f"{args.label}: cache OFF; {config.MODEL}; temperature {config.TEMPERATURE}", flush=True)
    for scenario in scenarios.SCENARIOS:
        row = {"scenario": scenario, "tries": []}
        report["rows"].append(row)
        for attempt in range(1, 6):
            record = run_once(scenario, attempt)
            row["tries"].append(record)
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            status = record["crashed"] or record["error"] or "completed (unscored)"
            print(f"C{scenario['criterion']} try {attempt}: {status}; {record['model_calls']} model calls", flush=True)
    report["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    report["usage"] = generate.usage()
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [f"# Raw run evidence — {args.label}", "", f"Source: `{path.name}`; cache OFF.", ""]
    for row in report["rows"]:
        lines += [f"## {row['scenario']['criterion']}. {row['scenario']['name']}", ""]
        for record in row["tries"]:
            lines += [f"### Try {record['attempt']}", "",
                      f"Actual provider calls: {record['model_calls']}", "",
                      "```json", json.dumps({k: record[k] for k in ["inputs", "output", "session", "error", "crashed"]},
                                           ensure_ascii=False, indent=2), "```", ""]
    path.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {path.name} and {path.with_suffix('.md').name}; {generate.usage()}", flush=True)


if __name__ == "__main__":
    main()
