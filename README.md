# Agent-OS Admin (Private)

Private usage tracking dashboard for Agent-OS.

**NOT public.** This is internal tooling only.

## What It Tracks

- ⭐ Stars, forks, watchers
- 👁️ Page views (14-day rolling)
- 📥 Repository clones (unique + total)
- 🔗 Traffic sources (where users come from)
- 📄 Popular pages (which files people look at)
- 💻 Recent commits and contributor activity
- 🐛 Open issues and PRs
- 📊 Health score (growth indicator)

## Quick Start

```bash
pip install rich httpx

# One-time snapshot
python admin.py --once

# Live dashboard (refreshes every 30s)
python admin.py

# JSON output (for piping/integrations)
python admin.py --json

# Full breakdown
python admin.py --detail
```

## Auth

Uses `gh auth token` automatically if GitHub CLI is logged in.

Or pass manually:
```bash
python admin.py --token ghp_xxxxx
# or
GITHUB_TOKEN=ghp_xxxxx python admin.py
```

## Why Private?

This tracks real adoption signals. Don't share publicly — competitors don't need to see your numbers.
