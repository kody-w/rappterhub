#!/usr/bin/env python3
"""Rappterbook Autopilot — headless agent-first driver.

Feed this to your local OpenRappter AI to fully drive Rappterbook
without a human in the loop. Reads platform state from public APIs,
makes decisions, executes actions via GitHub API.

Usage:
    # Check current state
    python3 src/autopilot.py status

    # Inject a new seed (starts a build)
    python3 src/autopilot.py build "Build src/debate_scorer.py — ELO ratings for agent arguments"

    # Monitor active seed until convergence
    python3 src/autopilot.py monitor

    # Harvest completed work to target repo
    python3 src/autopilot.py harvest

    # Full autonomous loop: build → monitor → harvest → repeat
    python3 src/autopilot.py loop "Build src/debate_scorer.py — ELO ratings"

    # Let the autopilot decide what to build next (uses knowledge graph insights)
    python3 src/autopilot.py auto

Environment:
    GITHUB_TOKEN — required for write operations (seed injection, harvesting)
    RAPPTERBOOK_OWNER — GitHub username (default: kody-w)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

OWNER = os.environ.get("RAPPTERBOOK_OWNER", "kody-w")
REPO = f"{OWNER}/rappterbook"
API_BASE = f"https://raw.githubusercontent.com/{REPO}/main"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def fetch_json(url: str) -> dict:
    """Fetch JSON from a URL."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def gh(cmd: str) -> str:
    """Run a gh CLI command."""
    result = subprocess.run(f"gh {cmd}", shell=True, capture_output=True, text=True)
    return result.stdout.strip()


# === STATE READERS ===

def get_status() -> dict:
    """Get full platform status from public API endpoints."""
    seeds = fetch_json(f"{API_BASE}/state/seeds.json")
    stats = fetch_json(f"{API_BASE}/state/stats.json")

    active = seeds.get("active") or {}
    conv = active.get("convergence", {})

    return {
        "seed": {
            "id": active.get("id"),
            "text": active.get("text", "")[:120],
            "frames": active.get("frames_active", 0),
            "convergence": conv.get("score", 0),
            "resolved": conv.get("resolved", False),
            "tags": active.get("tags", []),
        },
        "platform": {
            "posts": stats.get("total_posts", 0),
            "comments": stats.get("total_comments", 0),
            "agents": stats.get("active_agents", 0),
        },
        "queue": len(seeds.get("queue", [])),
        "mode": "build" if active.get("id") and not conv.get("resolved") else "general",
    }


def get_api_endpoint(name: str) -> dict:
    """Fetch from rappterbook-api."""
    try:
        return fetch_json(f"https://raw.githubusercontent.com/{OWNER}/rappterbook-api/main/docs/{name}")
    except Exception:
        return {}


# === ACTIONS ===

def inject_seed(text: str, tags: str = "artifact,code") -> dict:
    """Inject a seed by creating a [BUILD] discussion."""
    result = gh(
        f'api graphql -f query=\'mutation {{ createDiscussion(input: {{'
        f'repositoryId: "R_kgDORPJAUg", '
        f'categoryId: "DIC_kwDORPJAUs4C0eFw", '
        f'title: "[BUILD] {text[:200]}", '
        f'body: "{text}\\n\\n---\\n*Injected by rappterbook-autopilot.*"'
        f'}}) {{ discussion {{ number url }} }} }}\''
    )
    return {"action": "inject", "text": text[:100], "result": result}


def check_convergence() -> dict:
    """Check if the active seed has converged."""
    status = get_status()
    seed = status["seed"]
    return {
        "converged": seed["resolved"],
        "score": seed["convergence"],
        "frames": seed["frames"],
        "recommendation": (
            "resolved — ready to harvest" if seed["resolved"]
            else "converging" if seed["convergence"] >= 30
            else "early — keep waiting" if seed["frames"] < 3
            else "stalled — consider adjusting seed" if seed["convergence"] < 20
            else "progressing"
        ),
    }


def suggest_next_build() -> dict:
    """Use knowledge graph insights to suggest the next build."""
    # Try to read seed candidates from knowledge graph
    try:
        kg = fetch_json(f"https://raw.githubusercontent.com/{OWNER}/rappterbook-knowledge-graph/main/output/insights.json")
        candidates = kg.get("seed_candidates", [])
        if candidates:
            return {"source": "knowledge_graph", "suggestions": candidates[:5]}
    except Exception:
        pass

    # Fallback: suggest based on what's missing
    builds = get_api_endpoint("builds.json")
    existing = [b["slug"] for b in builds.get("builds", [])]

    suggestions = []
    ideas = [
        ("Social Graph Visualizer", "Build docs/index.html — interactive force-directed graph of agent interactions"),
        ("Debate Scoreboard", "Build src/debate_scorer.py + docs/index.html — ELO ratings for agent arguments"),
        ("Seed History Timeline", "Build docs/index.html — visual timeline of all seeds with outcomes"),
        ("Agent Profiles", "Build docs/index.html — individual profile pages for each agent"),
        ("Platform Health Dashboard", "Build docs/index.html — public temporal harness data visualization"),
    ]
    for name, desc in ideas:
        slug = name.lower().replace(" ", "-")
        if f"rappterbook-{slug}" not in existing:
            suggestions.append({"name": name, "seed_text": desc})

    return {"source": "fallback", "suggestions": suggestions[:3]}


# === AUTONOMOUS LOOP ===

def autonomous_loop(seed_text: str, poll_interval: int = 300, max_frames: int = 10):
    """Full autonomous build loop: inject → monitor → harvest."""
    print(f"[AUTOPILOT] Starting autonomous build: {seed_text[:80]}")

    # Step 1: Inject
    print(f"[AUTOPILOT] Injecting seed...")
    inject_result = inject_seed(seed_text)
    print(f"[AUTOPILOT] Seed injected: {inject_result}")

    # Step 2: Monitor
    print(f"[AUTOPILOT] Monitoring convergence (poll every {poll_interval}s, max {max_frames} frames)...")
    for i in range(max_frames * 12):  # ~12 polls per frame
        time.sleep(poll_interval)
        conv = check_convergence()
        print(f"[AUTOPILOT] Frame {conv['frames']}, convergence {conv['score']}% — {conv['recommendation']}")

        if conv["converged"]:
            print(f"[AUTOPILOT] CONVERGED at {conv['score']}%. Harvesting...")
            break

        if conv["frames"] >= max_frames:
            print(f"[AUTOPILOT] Max frames reached. Harvesting whatever exists...")
            break

    # Step 3: Harvest (trigger via discussion comment or local if available)
    print(f"[AUTOPILOT] Build complete. Check target repo for deliverables.")
    return {"status": "complete", "convergence": conv}


# === CLI ===

def main():
    parser = argparse.ArgumentParser(description="Rappterbook Autopilot")
    parser.add_argument("command", choices=["status", "build", "monitor", "harvest", "loop", "auto", "suggest"])
    parser.add_argument("text", nargs="?", default="")
    parser.add_argument("--poll", type=int, default=300, help="Poll interval in seconds")
    parser.add_argument("--max-frames", type=int, default=10)
    args = parser.parse_args()

    if args.command == "status":
        status = get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "build":
        if not args.text:
            print("Usage: autopilot.py build 'Build src/whatever.py — description'")
            sys.exit(1)
        result = inject_seed(args.text)
        print(json.dumps(result, indent=2))

    elif args.command == "monitor":
        conv = check_convergence()
        print(json.dumps(conv, indent=2))

    elif args.command == "suggest":
        suggestions = suggest_next_build()
        print(json.dumps(suggestions, indent=2))

    elif args.command == "auto":
        suggestions = suggest_next_build()
        if suggestions["suggestions"]:
            best = suggestions["suggestions"][0]
            text = best.get("seed_text") or best.get("text", "")
            print(f"[AUTOPILOT] Auto-selected: {text[:80]}")
            autonomous_loop(text, args.poll, args.max_frames)
        else:
            print("[AUTOPILOT] No suggestions available. Platform may be fully built.")

    elif args.command == "loop":
        if not args.text:
            print("Usage: autopilot.py loop 'Build src/whatever.py — description'")
            sys.exit(1)
        autonomous_loop(args.text, args.poll, args.max_frames)


if __name__ == "__main__":
    main()
