# Agent-OS Admin (Private)

Private usage tracking dashboard for Agent-OS.

**NOT public.** This is internal tooling only.

---

## 🔗 Quick Access

**Web Dashboard:** http://localhost:9000

```bash
python3 web.py --host 0.0.0.0 --port 9000
```

---

## What It Tracks

- ⭐ Stars, forks, watchers
- 👁️ Page views (14-day rolling)
- 📥 Repository clones (unique + total)
- 🔗 Traffic sources (where users come from)
- 📄 Popular pages (which files people look at)
- 💻 Recent commits and contributor activity
- 🐛 Open issues and PRs
- 📊 Health score (growth indicator)

## Two Ways to Use

### Web Dashboard (recommended)

```bash
python3 web.py --host 0.0.0.0 --port 9000
# Open: http://localhost:9000
```

Dark-themed dashboard with charts, auto-refreshes every 60s.

### Terminal Dashboard

```bash
# One-time snapshot
python3 admin.py --once

# Live dashboard (refreshes every 30s)
python3 admin.py

# JSON output
python3 admin.py --json

# Full breakdown
python3 admin.py --detail
```

## Auth

Uses `gh auth token` automatically if GitHub CLI is logged in.

Or pass manually:
```bash
python3 admin.py --token ghp_xxxxx
# or
GITHUB_TOKEN=ghp_xxxxx python3 admin.py
```

## Install

```bash
pip install rich httpx aiohttp
```

## Why Private?

This tracks real adoption signals. Don't share publicly — competitors don't need to see your numbers.
