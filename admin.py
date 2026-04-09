#!/usr/bin/env python3
"""
Agent-OS Admin Terminal
Real-time usage dashboard for tracking Agent-OS adoption.

Usage:
    python admin.py                  # Live dashboard (refreshes every 30s)
    python admin.py --once           # One-time snapshot
    python admin.py --json           # JSON output (for piping)
    python admin.py --detail         # Full breakdown
"""
import asyncio
import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

console = Console()

REPO = "factspark23-hash/Agent-OS"
GITHUB_API = "https://api.github.com"


class AgentOSStats:
    """Fetches real usage data from GitHub API."""

    def __init__(self, token: str = None):
        self.token = token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"

    async def fetch_all(self) -> dict:
        """Fetch all stats in parallel."""
        async with httpx.AsyncClient(timeout=30) as client:
            repo_task = self._get(client, f"/repos/{REPO}")
            traffic_views_task = self._get(client, f"/repos/{REPO}/traffic/views")
            traffic_clones_task = self._get(client, f"/repos/{REPO}/traffic/clones")
            referrers_task = self._get(client, f"/repos/{REPO}/traffic/popular/referrers")
            paths_task = self._get(client, f"/repos/{REPO}/traffic/popular/paths")
            releases_task = self._get(client, f"/repos/{REPO}/releases")
            contributors_task = self._get(client, f"/repos/{REPO}/contributors")
            issues_task = self._get(client, f"/repos/{REPO}/issues?state=open&per_page=100")
            prs_task = self._get(client, f"/repos/{REPO}/pulls?state=all&per_page=30")
            commits_task = self._get(client, f"/repos/{REPO}/commits?per_page=30")

            results = await asyncio.gather(
                repo_task, traffic_views_task, traffic_clones_task,
                referrers_task, paths_task, releases_task,
                contributors_task, issues_task, prs_task, commits_task,
                return_exceptions=True
            )

        return {
            "repo": results[0] if not isinstance(results[0], Exception) else {},
            "views": results[1] if not isinstance(results[1], Exception) else {},
            "clones": results[2] if not isinstance(results[2], Exception) else {},
            "referrers": results[3] if not isinstance(results[3], Exception) else [],
            "popular_paths": results[4] if not isinstance(results[4], Exception) else [],
            "releases": results[5] if not isinstance(results[5], Exception) else [],
            "contributors": results[6] if not isinstance(results[6], Exception) else [],
            "issues": results[7] if not isinstance(results[7], Exception) else [],
            "pulls": results[8] if not isinstance(results[8], Exception) else [],
            "commits": results[9] if not isinstance(results[9], Exception) else [],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _get(self, client: httpx.AsyncClient, path: str):
        resp = await client.get(f"{GITHUB_API}{path}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()


def format_number(n) -> str:
    """Format number with commas."""
    if n is None:
        return "0"
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def days_ago(iso_str: str) -> str:
    """Convert ISO timestamp to 'X days ago'."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        if delta.days == 0:
            hours = delta.seconds // 3600
            return f"{hours}h ago" if hours > 0 else "just now"
        if delta.days == 1:
            return "yesterday"
        return f"{delta.days}d ago"
    except:
        return iso_str


def render_dashboard(data: dict, detail: bool = False) -> Panel:
    """Render the full dashboard as a Rich Panel."""
    repo = data.get("repo", {})
    views = data.get("views", {})
    clones = data.get("clones", {})

    # ─── Header ─────────────────────────────────────────────
    header = Text()
    header.append("🤖 AGENT-OS ADMIN", style="bold cyan")
    header.append("  │  ", style="dim")
    header.append(f"Last updated: {days_ago(data.get('fetched_at', ''))}", style="dim")

    # ─── Core Metrics ───────────────────────────────────────
    metrics_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
    metrics_table.add_column("Metric", style="bold white")
    metrics_table.add_column("Value", justify="right")

    stars = repo.get("stargazerCount", 0) or 0
    forks = repo.get("forkCount", 0) or 0
    watchers_raw = repo.get("watchers", {})
    watchers = watchers_raw.get("totalCount", 0) if isinstance(watchers_raw, dict) else (watchers_raw or 0)
    open_issues = repo.get("issues", {}).get("totalCount", 0) if isinstance(repo.get("issues"), dict) else (repo.get("open_issues_count", 0) or 0)
    size_kb = repo.get("diskUsage", 0) or 0

    metrics_table.add_row("⭐ Stars", f"[yellow]{format_number(stars)}[/yellow]")
    metrics_table.add_row("🍴 Forks", f"[green]{format_number(forks)}[/green]")
    metrics_table.add_row("👀 Watchers", f"[blue]{format_number(watchers)}[/blue]")
    metrics_table.add_row("🐛 Open Issues", f"[red]{format_number(open_issues)}[/red]")
    metrics_table.add_row("📦 Repo Size", f"{format_number(size_kb)} KB")

    # ─── Traffic (14 days) ──────────────────────────────────
    traffic_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
    traffic_table.add_column("Metric", style="bold white")
    traffic_table.add_column("Total", justify="right")
    traffic_table.add_column("Unique", justify="right")

    view_data = views.get("views", [])
    clone_data = clones.get("clones", [])

    total_views = sum(v.get("count", 0) for v in view_data)
    unique_views = sum(v.get("uniques", 0) for v in view_data)
    total_clones = sum(c.get("count", 0) for c in clone_data)
    unique_clones = sum(c.get("uniques", 0) for c in clone_data)

    traffic_table.add_row("👁️ Page Views (14d)", format_number(total_views), format_number(unique_views))
    traffic_table.add_row("📥 Clones (14d)", format_number(total_clones), format_number(unique_clones))

    # ─── Daily Breakdown (last 7 days) ─────────────────────
    daily_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    daily_table.add_column("Date", style="dim")
    daily_table.add_column("Views", justify="right", style="cyan")
    daily_table.add_column("Unique V", justify="right", style="cyan dim")
    daily_table.add_column("Clones", justify="right", style="green")
    daily_table.add_column("Unique C", justify="right", style="green dim")

    # Last 7 days
    for v, c in zip(view_data[-7:], clone_data[-7:]):
        date_str = v.get("timestamp", "")[:10]
        daily_table.add_row(
            date_str,
            str(v.get("count", 0)),
            str(v.get("uniques", 0)),
            str(c.get("count", 0)),
            str(c.get("uniques", 0)),
        )

    # ─── Traffic Sources ────────────────────────────────────
    referrers = data.get("referrers", [])
    ref_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    ref_table.add_column("Source", style="bold")
    ref_table.add_column("Views", justify="right")
    ref_table.add_column("Unique", justify="right")

    for ref in referrers[:10]:
        ref_table.add_row(
            ref.get("referrer", "unknown"),
            str(ref.get("count", 0)),
            str(ref.get("uniques", 0)),
        )

    # ─── Popular Pages ──────────────────────────────────────
    paths = data.get("popular_paths", [])
    path_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    path_table.add_column("Path", style="bold")
    path_table.add_column("Views", justify="right")
    path_table.add_column("Unique", justify="right")

    for p in paths[:10]:
        path_table.add_row(
            p.get("path", "/"),
            str(p.get("count", 0)),
            str(p.get("uniques", 0)),
        )

    # ─── Recent Activity ────────────────────────────────────
    commits = data.get("commits", [])
    commit_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    commit_table.add_column("When", style="dim", width=10)
    commit_table.add_column("Author", style="bold")
    commit_table.add_column("Message", max_width=50)

    for c in commits[:10]:
        sha_data = c.get("commit", {})
        author = sha_data.get("author", {})
        msg = sha_data.get("message", "").split("\n")[0][:50]
        commit_table.add_row(
            days_ago(author.get("date", "")),
            author.get("name", "unknown"),
            msg,
        )

    # ─── Contributors ───────────────────────────────────────
    contributors = data.get("contributors", [])
    contrib_count = len(contributors)

    # ─── Open Issues Preview ────────────────────────────────
    issues = data.get("issues", [])
    issue_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    issue_table.add_column("#", style="dim", width=6)
    issue_table.add_column("Title", max_width=50)
    issue_table.add_column("Author", style="dim")

    for issue in issues[:5]:
        issue_table.add_row(
            f"#{issue.get('number', '')}",
            issue.get("title", "")[:50],
            issue.get("user", {}).get("login", ""),
        )

    # ─── PRs ────────────────────────────────────────────────
    pulls = data.get("pulls", [])
    pr_merged = sum(1 for p in pulls if p.get("merged_at"))
    pr_open = sum(1 for p in pulls if p.get("state") == "open" and not p.get("merged_at"))

    # ─── Health Score ───────────────────────────────────────
    score = 0
    if stars > 0: score += min(stars, 50)
    if forks > 0: score += min(forks * 5, 50)
    if unique_clones > 0: score += min(unique_clones, 50)
    if contrib_count > 1: score += min(contrib_count * 10, 50)
    if open_issues > 0: score += 10  # People care enough to file issues

    if score >= 100:
        health = "[bold green]🔥 HOT[/bold green]"
    elif score >= 50:
        health = "[bold yellow]📈 GROWING[/bold yellow]"
    elif score >= 10:
        health = "[bold blue]🌱 EARLY[/bold blue]"
    else:
        health = "[dim]💤 SLEEPING[/dim]"

    # ─── Build Layout ──────────────────────────────────────
    layout_text = Text()
    layout_text.append(header)
    layout_text.append("\n\n")

    # Health
    layout_text.append("Project Health: ", style="bold")
    layout_text.append(f"{health}  (score: {score})\n\n")

    # Create sections
    sections = []

    # Top row: metrics + traffic
    top_table = Table(box=None, show_header=False, pad_edge=False)
    top_table.add_column("left", ratio=1)
    top_table.add_column("right", ratio=1)
    top_table.add_row(
        Panel(metrics_table, title="📊 Core Metrics", border_style="cyan"),
        Panel(traffic_table, title="📈 Traffic (14 days)", border_style="green"),
    )
    sections.append(top_table)

    # Daily breakdown
    sections.append(Panel(daily_table, title="📅 Daily Breakdown (Last 7 Days)", border_style="blue"))

    if detail:
        # Traffic sources + popular pages side by side
        detail_table = Table(box=None, show_header=False, pad_edge=False)
        detail_table.add_column("left", ratio=1)
        detail_table.add_column("right", ratio=1)

        ref_panel = Panel(ref_table, title="🔗 Traffic Sources", border_style="yellow") if referrers else Panel("[dim]No referrer data[/dim]", title="🔗 Traffic Sources")
        path_panel = Panel(path_table, title="📄 Popular Pages", border_style="magenta") if paths else Panel("[dim]No path data[/dim]", title="📄 Popular Pages")
        detail_table.add_row(ref_panel, path_panel)
        sections.append(detail_table)

    # Activity
    sections.append(Panel(commit_table, title="💻 Recent Commits", border_style="cyan"))

    # Bottom row: contributors + PRs
    bottom_text = Text()
    bottom_text.append(f"👥 Contributors: {contrib_count}", style="bold")
    bottom_text.append(f"    🔄 PRs: {pr_open} open, {pr_merged} merged", style="bold")
    bottom_text.append(f"    🐛 Issues: {open_issues} open", style="bold")

    sections.append(Panel(bottom_text, title="📋 Summary", border_style="green"))

    if issues and detail:
        sections.append(Panel(issue_table, title="🐛 Open Issues", border_style="red"))

    # Combine all
    from rich.console import Group
    return Panel(
        Group(*sections),
        title=header,
        border_style="cyan",
        padding=(1, 2),
    )


def render_json(data: dict) -> str:
    """Render stats as JSON."""
    repo = data.get("repo", {})
    views = data.get("views", {})
    clones = data.get("clones", {})

    view_data = views.get("views", [])
    clone_data = clones.get("clones", [])

    output = {
        "repo": REPO,
        "fetched_at": data.get("fetched_at"),
        "stars": repo.get("stargazerCount", 0),
        "forks": repo.get("forkCount", 0),
        "watchers": repo.get("watchers", {}).get("totalCount", 0),
        "open_issues": repo.get("issues", {}).get("totalCount", 0),
        "traffic_14d": {
            "total_views": sum(v.get("count", 0) for v in view_data),
            "unique_views": sum(v.get("uniques", 0) for v in view_data),
            "total_clones": sum(c.get("count", 0) for c in clone_data),
            "unique_clones": sum(c.get("uniques", 0) for c in clone_data),
        },
        "contributors": len(data.get("contributors", [])),
        "referrers": data.get("referrers", []),
        "popular_paths": data.get("popular_paths", []),
        "recent_commits": [
            {
                "message": c.get("commit", {}).get("message", "").split("\n")[0],
                "author": c.get("commit", {}).get("author", {}).get("name"),
                "date": c.get("commit", {}).get("author", {}).get("date"),
            }
            for c in data.get("commits", [])[:10]
        ],
    }
    return json.dumps(output, indent=2)


async def run_once(detail: bool = False, as_json: bool = False, token: str = None):
    """Fetch and display stats once."""
    stats = AgentOSStats(token=token)

    if not as_json:
        console.print("[dim]Fetching GitHub data...[/dim]")

    data = await stats.fetch_all()

    if as_json:
        print(render_json(data))
    else:
        panel = render_dashboard(data, detail=detail)
        console.clear()
        console.print(panel)

    return data


async def run_live(detail: bool = False, interval: int = 30, token: str = None):
    """Live refreshing dashboard."""
    stats = AgentOSStats(token=token)

    while True:
        try:
            data = await stats.fetch_all()
            panel = render_dashboard(data, detail=detail)
            console.clear()
            console.print(panel)
            console.print(f"\n[dim]Refreshing in {interval}s... (Ctrl+C to quit)[/dim]")
            await asyncio.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Agent-OS Admin Dashboard")
    parser.add_argument("--once", action="store_true", help="One-time snapshot (no live refresh)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--detail", action="store_true", help="Show full breakdown")
    parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds (default: 30)")
    parser.add_argument("--token", type=str, help="GitHub token (or set GITHUB_TOKEN env var)")
    args = parser.parse_args()

    import os
    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    if not token:
        # Try to get from gh CLI
        try:
            import subprocess
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            if result.returncode == 0:
                token = result.stdout.strip()
        except:
            pass

    if args.json or args.once:
        asyncio.run(run_once(detail=args.detail, as_json=args.json, token=token))
    else:
        asyncio.run(run_live(detail=args.detail, interval=args.interval, token=token))


if __name__ == "__main__":
    main()
