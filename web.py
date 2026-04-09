#!/usr/bin/env python3
"""
Agent-OS Admin — Web Dashboard
Host a web dashboard you can open in your browser.

Usage:
    python web.py                    # Default: http://localhost:9000
    python web.py --port 8080        # Custom port
    python web.py --host 0.0.0.0     # Access from other devices on network
"""
import asyncio
import argparse
import json
import os
import time
from datetime import datetime, timezone

from aiohttp import web
import httpx

REPO = "factspark23-hash/Agent-OS"
GITHUB_API = "https://api.github.com"


class StatsFetcher:
    def __init__(self, token=None):
        self.token = token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"
        self._cache = {}
        self._cache_time = 0
        self._cache_ttl = 60  # cache for 60 seconds

    async def fetch_all(self):
        now = time.time()
        if self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache

        async with httpx.AsyncClient(timeout=30) as client:
            endpoints = {
                "repo": f"/repos/{REPO}",
                "views": f"/repos/{REPO}/traffic/views",
                "clones": f"/repos/{REPO}/traffic/clones",
                "referrers": f"/repos/{REPO}/traffic/popular/referrers",
                "paths": f"/repos/{REPO}/traffic/popular/paths",
                "releases": f"/repos/{REPO}/releases",
                "contributors": f"/repos/{REPO}/contributors",
                "issues": f"/repos/{REPO}/issues?state=open&per_page=100",
                "pulls": f"/repos/{REPO}/pulls?state=all&per_page=30",
                "commits": f"/repos/{REPO}/commits?per_page=20",
            }

            tasks = {}
            for key, path in endpoints.items():
                tasks[key] = self._get(client, path)

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        data = {}
        for key, result in zip(tasks.keys(), results):
            data[key] = result if not isinstance(result, Exception) else {}

        data["fetched_at"] = datetime.now(timezone.utc).isoformat()
        self._cache = data
        self._cache_time = now
        return data

    async def _get(self, client, path):
        resp = await client.get(f"{GITHUB_API}{path}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()


fetcher = StatsFetcher()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent-OS Admin</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0d1117;
    color: #e6edf3;
    min-height: 100vh;
}
.header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border-bottom: 1px solid #30363d;
    padding: 20px 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header h1 {
    font-size: 24px;
    font-weight: 600;
}
.header h1 span { color: #58a6ff; }
.header .meta {
    font-size: 13px;
    color: #8b949e;
}
.header .status {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #3fb950;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}
.card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
    transition: border-color 0.2s;
}
.card:hover { border-color: #58a6ff; }
.card .label {
    font-size: 13px;
    color: #8b949e;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.card .value {
    font-size: 36px;
    font-weight: 700;
    color: #e6edf3;
}
.card .sub {
    font-size: 12px;
    color: #8b949e;
    margin-top: 4px;
}
.card.stars .value { color: #f0c040; }
.card.forks .value { color: #3fb950; }
.card.clones .value { color: #58a6ff; }
.card.views .value { color: #bc8cff; }
.card.issues .value { color: #f85149; }
.card.contributors .value { color: #f778ba; }

.section {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    margin-bottom: 24px;
    overflow: hidden;
}
.section-header {
    padding: 16px 20px;
    border-bottom: 1px solid #30363d;
    font-weight: 600;
    font-size: 15px;
}
.section-body { padding: 0; }
table {
    width: 100%;
    border-collapse: collapse;
}
th {
    text-align: left;
    padding: 10px 16px;
    font-size: 12px;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #30363d;
}
td {
    padding: 10px 16px;
    font-size: 14px;
    border-bottom: 1px solid #21262d;
}
tr:last-child td { border-bottom: none; }
tr:hover { background: #1c2128; }
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
}
.badge.green { background: #238636; color: #fff; }
.badge.red { background: #da3633; color: #fff; }
.badge.blue { background: #1f6feb; color: #fff; }
.badge.purple { background: #8957e5; color: #fff; }
.badge.yellow { background: #9e6a03; color: #fff; }
.bar-container {
    display: flex;
    align-items: center;
    gap: 8px;
}
.bar {
    height: 20px;
    background: #21262d;
    border-radius: 4px;
    overflow: hidden;
    flex: 1;
}
.bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}
.bar-fill.views { background: linear-gradient(90deg, #58a6ff, #bc8cff); }
.bar-fill.clones { background: linear-gradient(90deg, #3fb950, #58a6ff); }
.bar-val {
    font-size: 13px;
    color: #8b949e;
    min-width: 50px;
    text-align: right;
}
.health {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 600;
}
.health.growing { background: #23863620; color: #3fb950; border: 1px solid #23863640; }
.health.early { background: #1f6feb20; color: #58a6ff; border: 1px solid #1f6feb40; }
.health.sleeping { background: #30363d40; color: #8b949e; border: 1px solid #30363d; }
.refresh-btn {
    background: #21262d;
    border: 1px solid #30363d;
    color: #e6edf3;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
}
.refresh-btn:hover { background: #30363d; }
.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}
@media (max-width: 768px) {
    .two-col { grid-template-columns: 1fr; }
    .grid { grid-template-columns: 1fr 1fr; }
}
.loading {
    text-align: center;
    padding: 60px;
    color: #8b949e;
}
.loading .spinner {
    display: inline-block;
    width: 32px;
    height: 32px;
    border: 3px solid #30363d;
    border-top-color: #58a6ff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>

<div class="header">
    <h1>🤖 Agent-OS <span>Admin</span></h1>
    <div class="meta">
        <span class="status"></span>
        <span id="updated">Loading...</span>
        <button class="refresh-btn" onclick="loadData()" style="margin-left: 12px;">↻ Refresh</button>
    </div>
</div>

<div class="container">
    <div id="loading" class="loading">
        <div class="spinner"></div>
        <div>Fetching GitHub data...</div>
    </div>

    <div id="dashboard" style="display:none;">
        <!-- Health -->
        <div style="margin-bottom: 24px;">
            <span id="health-badge" class="health early">🌱 EARLY</span>
            <span style="margin-left: 12px; color: #8b949e; font-size: 14px;">Score: <span id="health-score">0</span></span>
        </div>

        <!-- Core Metrics -->
        <div class="grid">
            <div class="card stars">
                <div class="label">⭐ Stars</div>
                <div class="value" id="stars">0</div>
                <div class="sub">People who starred the repo</div>
            </div>
            <div class="card forks">
                <div class="label">🍴 Forks</div>
                <div class="value" id="forks">0</div>
                <div class="sub">People who forked the repo</div>
            </div>
            <div class="card clones">
                <div class="label">📥 Clones (14d)</div>
                <div class="value" id="clones">0</div>
                <div class="sub"><span id="unique-clones">0</span> unique</div>
            </div>
            <div class="card views">
                <div class="label">👁️ Views (14d)</div>
                <div class="value" id="views">0</div>
                <div class="sub"><span id="unique-views">0</span> unique visitors</div>
            </div>
            <div class="card issues">
                <div class="label">🐛 Open Issues</div>
                <div class="value" id="issues">0</div>
                <div class="sub">Feature requests & bugs</div>
            </div>
            <div class="card contributors">
                <div class="label">👥 Contributors</div>
                <div class="value" id="contributors">0</div>
                <div class="sub">People who committed code</div>
            </div>
        </div>

        <!-- Daily Chart -->
        <div class="section">
            <div class="section-header">📅 Daily Traffic (Last 14 Days)</div>
            <div class="section-body" id="daily-chart" style="padding: 20px;"></div>
        </div>

        <div class="two-col">
            <!-- Traffic Sources -->
            <div class="section">
                <div class="section-header">🔗 Traffic Sources</div>
                <div class="section-body">
                    <table>
                        <thead><tr><th>Source</th><th>Views</th><th>Unique</th></tr></thead>
                        <tbody id="referrers-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Popular Pages -->
            <div class="section">
                <div class="section-header">📄 Popular Pages</div>
                <div class="section-body">
                    <table>
                        <thead><tr><th>Path</th><th>Views</th><th>Unique</th></tr></thead>
                        <tbody id="paths-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Recent Commits -->
        <div class="section">
            <div class="section-header">💻 Recent Commits</div>
            <div class="section-body">
                <table>
                    <thead><tr><th>When</th><th>Author</th><th>Message</th></tr></thead>
                    <tbody id="commits-body"></tbody>
                </table>
            </div>
        </div>

        <!-- Open Issues -->
        <div class="section">
            <div class="section-header">🐛 Open Issues</div>
            <div class="section-body">
                <table>
                    <thead><tr><th>#</th><th>Title</th><th>Author</th><th>Labels</th></tr></thead>
                    <tbody id="issues-body"></tbody>
                </table>
            </div>
        </div>

        <!-- PRs -->
        <div class="section">
            <div class="section-header">🔄 Pull Requests</div>
            <div class="section-body">
                <table>
                    <thead><tr><th>#</th><th>Title</th><th>Author</th><th>Status</th></tr></thead>
                    <tbody id="prs-body"></tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
function daysAgo(iso) {
    const d = new Date(iso);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 3600) return Math.floor(diff/60) + 'm ago';
    if (diff < 86400) return Math.floor(diff/3600) + 'h ago';
    return Math.floor(diff/86400) + 'd ago';
}

function fmt(n) {
    if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n/1000).toFixed(1) + 'K';
    return n.toString();
}

async function loadData() {
    try {
        const resp = await fetch('/api/stats');
        const d = await resp.json();

        document.getElementById('loading').style.display = 'none';
        document.getElementById('dashboard').style.display = 'block';

        const repo = d.repo || {};
        const views = d.views || {};
        const clones = d.clones || {};
        const viewData = views.views || [];
        const cloneData = clones.clones || [];

        // Update timestamp
        document.getElementById('updated').textContent = 'Updated: ' + daysAgo(d.fetched_at);

        // Core metrics
        document.getElementById('stars').textContent = fmt(repo.stargazerCount || 0);
        document.getElementById('forks').textContent = fmt(repo.forkCount || 0);
        const totalViews = viewData.reduce((s, v) => s + (v.count || 0), 0);
        const uniqueViews = viewData.reduce((s, v) => s + (v.uniques || 0), 0);
        const totalClones = cloneData.reduce((s, v) => s + (v.count || 0), 0);
        const uniqueClones = cloneData.reduce((s, v) => s + (v.uniques || 0), 0);
        document.getElementById('views').textContent = fmt(totalViews);
        document.getElementById('unique-views').textContent = fmt(uniqueViews);
        document.getElementById('clones').textContent = fmt(totalClones);
        document.getElementById('unique-clones').textContent = fmt(uniqueClones);

        const openIssues = (repo.issues && repo.issues.totalCount) || repo.open_issues_count || 0;
        document.getElementById('issues').textContent = openIssues;
        document.getElementById('contributors').textContent = (d.contributors || []).length;

        // Health
        let score = 0;
        const stars = repo.stargazerCount || 0;
        const forks = repo.forkCount || 0;
        score += Math.min(stars, 50) + Math.min(forks * 5, 50) + Math.min(uniqueClones, 50);
        const contribCount = (d.contributors || []).length;
        score += Math.min(contribCount * 10, 50);
        if (openIssues > 0) score += 10;
        document.getElementById('health-score').textContent = score;
        const hb = document.getElementById('health-badge');
        if (score >= 100) { hb.className = 'health growing'; hb.textContent = '🔥 HOT'; }
        else if (score >= 50) { hb.className = 'health growing'; hb.textContent = '📈 GROWING'; }
        else if (score >= 10) { hb.className = 'health early'; hb.textContent = '🌱 EARLY'; }
        else { hb.className = 'health sleeping'; hb.textContent = '💤 SLEEPING'; }

        // Daily chart
        const maxVal = Math.max(...viewData.map(v => v.count || 0), ...cloneData.map(c => c.count || 0), 1);
        let chartHtml = '<div style="display:flex; gap:4px; align-items:flex-end; height:120px;">';
        viewData.forEach((v, i) => {
            const c = cloneData[i] || {};
            const vh = Math.max(2, ((v.count || 0) / maxVal) * 100);
            const ch = Math.max(2, ((c.count || 0) / maxVal) * 100);
            const date = (v.timestamp || '').slice(5, 10);
            chartHtml += `<div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:2px;">
                <div style="display:flex; gap:1px; align-items:flex-end; height:100px;">
                    <div style="width:8px; height:${vh}px; background:linear-gradient(180deg,#bc8cff,#58a6ff); border-radius:3px 3px 0 0;" title="Views: ${v.count||0}"></div>
                    <div style="width:8px; height:${ch}px; background:linear-gradient(180deg,#58a6ff,#3fb950); border-radius:3px 3px 0 0;" title="Clones: ${c.count||0}"></div>
                </div>
                <div style="font-size:10px; color:#8b949e;">${date}</div>
            </div>`;
        });
        chartHtml += '</div>';
        chartHtml += '<div style="margin-top:8px; font-size:12px; color:#8b949e;"><span style="color:#bc8cff;">■</span> Views &nbsp; <span style="color:#3fb950;">■</span> Clones</div>';
        document.getElementById('daily-chart').innerHTML = chartHtml;

        // Referrers
        const refBody = document.getElementById('referrers-body');
        refBody.innerHTML = '';
        (d.referrers || []).forEach(r => {
            refBody.innerHTML += `<tr><td>${r.referrer || '—'}</td><td>${r.count || 0}</td><td>${r.uniques || 0}</td></tr>`;
        });
        if (!(d.referrers || []).length) refBody.innerHTML = '<tr><td colspan="3" style="color:#8b949e;">No referrer data yet</td></tr>';

        // Popular paths
        const pathBody = document.getElementById('paths-body');
        pathBody.innerHTML = '';
        (d.paths || []).forEach(p => {
            pathBody.innerHTML += `<tr><td style="font-family:monospace; font-size:13px;">${(p.path || '/').slice(0, 40)}</td><td>${p.count || 0}</td><td>${p.uniques || 0}</td></tr>`;
        });
        if (!(d.paths || []).length) pathBody.innerHTML = '<tr><td colspan="3" style="color:#8b949e;">No path data yet</td></tr>';

        // Commits
        const commitBody = document.getElementById('commits-body');
        commitBody.innerHTML = '';
        (d.commits || []).forEach(c => {
            const commit = c.commit || {};
            const author = commit.author || {};
            const msg = (commit.message || '').split('\\n')[0].slice(0, 60);
            commitBody.innerHTML += `<tr><td style="color:#8b949e;">${daysAgo(author.date || '')}</td><td>${author.name || '—'}</td><td>${msg}</td></tr>`;
        });

        // Issues
        const issueBody = document.getElementById('issues-body');
        issueBody.innerHTML = '';
        (d.issues || []).forEach(i => {
            const labels = (i.labels || []).map(l => `<span class="badge" style="background:#${l.color || '30363d'}20; color:#${l.color || '8b949e'}; border:1px solid #${l.color || '30363d'}40;">${l.name}</span>`).join(' ');
            issueBody.innerHTML += `<tr><td style="color:#8b949e;">#${i.number}</td><td>${(i.title || '').slice(0, 60)}</td><td style="color:#8b949e;">${(i.user || {}).login || '—'}</td><td>${labels}</td></tr>`;
        });

        // PRs
        const prBody = document.getElementById('prs-body');
        prBody.innerHTML = '';
        (d.pulls || []).forEach(p => {
            let status = '<span class="badge green">merged</span>';
            if (!p.merged_at && p.state === 'open') status = '<span class="badge blue">open</span>';
            else if (p.state === 'closed' && !p.merged_at) status = '<span class="badge red">closed</span>';
            prBody.innerHTML += `<tr><td style="color:#8b949e;">#${p.number}</td><td>${(p.title || '').slice(0, 60)}</td><td style="color:#8b949e;">${(p.user || {}).login || '—'}</td><td>${status}</td></tr>`;
        });

    } catch (e) {
        document.getElementById('loading').innerHTML = '<div style="color:#f85149;">Error: ' + e.message + '</div>';
    }
}

loadData();
setInterval(loadData, 60000); // Auto-refresh every 60s
</script>
</body>
</html>"""


async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html")


async def handle_stats(request):
    try:
        data = await fetcher.fetch_all()
        return web.json_response(data)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_status(request):
    return web.json_response({"status": "running", "repo": REPO})


def create_app():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/stats", handle_stats)
    app.router.add_get("/api/status", handle_status)
    return app


def main():
    parser = argparse.ArgumentParser(description="Agent-OS Admin Web Dashboard")
    parser.add_argument("--port", type=int, default=9000, help="Port (default: 9000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host (default: 127.0.0.1)")
    args = parser.parse_args()

    print(f"\n  🤖 Agent-OS Admin Dashboard")
    print(f"  ─────────────────────────────────────────")
    print(f"  Open in browser: http://localhost:{args.port}")
    print(f"  Press Ctrl+C to stop")
    print(f"  ─────────────────────────────────────────\n")

    app = create_app()
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
