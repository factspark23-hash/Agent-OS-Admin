#!/usr/bin/env python3
"""Fetch all Agent-OS GitHub stats and save to data.json"""
import json, urllib.request, os, sys
from datetime import datetime, timezone

REPO = "factspark23-hash/Agent-OS"
API = "https://api.github.com"
TOKEN = os.environ.get("GH_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {TOKEN}",
    "User-Agent": "Agent-OS-Admin"
}

def get(path):
    url = f"{API}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  ⚠️ {path}: {e}", file=sys.stderr)
        return {}

endpoints = {
    "repo":        f"/repos/{REPO}",
    "views":       f"/repos/{REPO}/traffic/views",
    "clones":      f"/repos/{REPO}/traffic/clones",
    "referrers":   f"/repos/{REPO}/traffic/popular/referrers",
    "popular_paths": f"/repos/{REPO}/traffic/popular/paths",
    "releases":    f"/repos/{REPO}/releases",
    "contributors":f"/repos/{REPO}/contributors",
    "issues":      f"/repos/{REPO}/issues?state=open&per_page=100",
    "pulls":       f"/repos/{REPO}/pulls?state=all&per_page=30",
    "commits":     f"/repos/{REPO}/commits?per_page=20",
}

print("Fetching data from GitHub API...")
data = {}
for key, path in endpoints.items():
    print(f"  → {key}")
    data[key] = get(path)

data["fetched_at"] = datetime.now(timezone.utc).isoformat()

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"\n✅ data.json updated at {data['fetched_at']}")
