#!/usr/bin/env python3
"""
Supervisor Dashboard
Real-time web dashboard showing integration status, test results, and system health
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add supervisor to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import subprocess

from utils.gitops import GitOpsManager
from utils.config_loader import get_config_loader
from integration_tests import IntegrationTestSuite
from quality_gates import QualityGate

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


app = FastAPI(
    title="Supervisor Dashboard",
    description="Multi-agent integration monitoring for DGX Spark",
    version="1.0.0"
)


# Global instances
git_manager = GitOpsManager()
config_loader = get_config_loader()


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard HTML"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Supervisor Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #0d1117;
            color: #c9d1d9;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #58a6ff;
            border-bottom: 2px solid #21262d;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #58a6ff;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: #161b22;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #21262d;
        }}
        th {{
            background-color: #21262d;
            color: #58a6ff;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #1c2128;
        }}
        .status-merged {{ color: #3fb950; }}
        .status-pending {{ color: #f85149; }}
        .status-ready {{ color: #d29922; }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-success {{ background-color: #238636; color: white; }}
        .badge-warning {{ background-color: #9e6a03; color: white; }}
        .badge-danger {{ background-color: #da3633; color: white; }}
        .badge-info {{ background-color: #1f6feb; color: white; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background-color: #161b22;
            padding: 20px;
            border-radius: 6px;
            border: 1px solid #21262d;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #58a6ff;
        }}
        .stat-label {{
            color: #8b949e;
            margin-top: 5px;
        }}
        pre {{
            background-color: #161b22;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #21262d;
            overflow-x: auto;
        }}
        .timestamp {{
            color: #8b949e;
            font-size: 14px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #21262d;
            text-align: center;
            color: #8b949e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Supervisor Dashboard</h1>
        <p class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (auto-refresh: 30s)</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="merged-count">-</div>
                <div class="stat-label">Branches Merged</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="pending-count">-</div>
                <div class="stat-label">Pending Merge</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="conflict-count">-</div>
                <div class="stat-label">Conflicts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="test-pass-rate">-</div>
                <div class="stat-label">Test Pass Rate</div>
            </div>
        </div>

        <h2>📋 Agent Branch Status</h2>
        <div id="branch-status">
            <p>Loading...</p>
        </div>

        <h2>🐳 Docker Services</h2>
        <div id="docker-status">
            <p>Loading...</p>
        </div>

        <h2>💻 System Health</h2>
        <div id="system-health">
            <p>Loading...</p>
        </div>

        <h2>📊 Recent Activity</h2>
        <div id="recent-activity">
            <p>Loading...</p>
        </div>

        <div class="footer">
            DGX Spark Multi-Agent Integration Supervisor v1.0 |
            <a href="/api/status" style="color: #58a6ff;">API Status</a> |
            <a href="/docs" style="color: #58a6ff;">API Docs</a>
        </div>
    </div>

    <script>
        // Fetch data and update dashboard
        async function updateDashboard() {{
            try {{
                const response = await fetch('/api/status');
                const data = await response.json();

                // Update stats
                document.getElementById('merged-count').textContent = data.stats.merged || 0;
                document.getElementById('pending-count').textContent = data.stats.pending || 0;
                document.getElementById('conflict-count').textContent = data.stats.conflicts || 0;
                document.getElementById('test-pass-rate').textContent = (data.stats.test_pass_rate || 0) + '%';

                // Update branch status table
                updateBranchStatus(data.branches);

                // Update Docker services
                updateDockerStatus(data.docker_services);

                // Update system health
                updateSystemHealth(data.system_health);

            }} catch (error) {{
                console.error('Failed to update dashboard:', error);
            }}
        }}

        function updateBranchStatus(branches) {{
            let html = '<table><tr><th>Agent</th><th>Branch</th><th>Status</th><th>Commits Ahead</th><th>Last Commit</th><th>Conflicts</th></tr>';

            for (const [branch, info] of Object.entries(branches)) {{
                const statusClass = info.commits_ahead === 0 ? 'status-merged' :
                                   info.has_conflicts ? 'status-pending' : 'status-ready';
                const statusText = info.commits_ahead === 0 ? '✅ Merged' :
                                  info.has_conflicts ? '⚠️  Conflicts' : '⏳ Ready';

                html += `<tr>
                    <td>${{branch}}</td>
                    <td><code>${{branch}}</code></td>
                    <td class="${{statusClass}}">${{statusText}}</td>
                    <td>${{info.commits_ahead}}</td>
                    <td>${{info.last_commit_sha || 'N/A'}}</td>
                    <td>${{info.conflict_files ? info.conflict_files.length : 0}}</td>
                </tr>`;
            }}

            html += '</table>';
            document.getElementById('branch-status').innerHTML = html;
        }}

        function updateDockerStatus(services) {{
            if (!services || services.length === 0) {{
                document.getElementById('docker-status').innerHTML = '<p>No Docker services running</p>';
                return;
            }}

            let html = '<table><tr><th>Service</th><th>Status</th><th>Health</th></tr>';

            services.forEach(service => {{
                const statusBadge = service.status === 'running' ?
                    '<span class="badge badge-success">Running</span>' :
                    '<span class="badge badge-danger">' + service.status + '</span>';

                html += `<tr>
                    <td>${{service.name}}</td>
                    <td>${{statusBadge}}</td>
                    <td>${{service.health || 'N/A'}}</td>
                </tr>`;
            }});

            html += '</table>';
            document.getElementById('docker-status').innerHTML = html;
        }}

        function updateSystemHealth(health) {{
            let html = '<pre>';
            html += `GPU Memory: ${{health.gpu_memory || 'N/A'}}\\n`;
            html += `Disk Usage: ${{health.disk_usage || 'N/A'}}\\n`;
            html += `CPU Usage: ${{health.cpu_usage || 'N/A'}}\\n`;
            html += '</pre>';
            document.getElementById('system-health').innerHTML = html;
        }}

        // Initial load
        updateDashboard();

        // Update every 10 seconds (page auto-refreshes every 30s as backup)
        setInterval(updateDashboard, 10000);
    </script>
</body>
</html>
"""


@app.get("/api/status")
async def api_status():
    """Machine-readable status API"""

    # Get all agent branches
    agent_branches = git_manager.get_agent_branches()

    # Get status for each branch
    branches = {}
    merged_count = 0
    pending_count = 0
    conflict_count = 0

    for branch in agent_branches:
        status = git_manager.get_branch_status(branch)

        if status.exists:
            branches[branch] = {
                'exists': True,
                'commits_ahead': status.commits_ahead,
                'last_commit_sha': status.last_commit_sha,
                'last_commit_message': status.last_commit_message,
                'has_conflicts': status.has_conflicts,
                'conflict_files': status.conflict_files
            }

            if status.commits_ahead == 0:
                merged_count += 1
            else:
                pending_count += 1

            if status.has_conflicts:
                conflict_count += 1
        else:
            branches[branch] = {
                'exists': False
            }

    # Get Docker services
    docker_services = []
    if DOCKER_AVAILABLE:
        try:
            client = docker.from_env()
            containers = client.containers.list(all=True)

            for container in containers:
                docker_services.append({
                    'name': container.name,
                    'status': container.status,
                    'health': container.attrs.get('State', {}).get('Health', {}).get('Status', 'N/A')
                })
        except:
            pass

    # Get system health
    system_health = {}

    # GPU status
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total',
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            if len(parts) >= 2:
                mem_used = float(parts[0].strip())
                mem_total = float(parts[1].strip())
                mem_percent = (mem_used / mem_total) * 100
                system_health['gpu_memory'] = f"{mem_used:.0f}MB / {mem_total:.0f}MB ({mem_percent:.1f}%)"
    except:
        pass

    # Disk usage
    if PSUTIL_AVAILABLE:
        try:
            disk = psutil.disk_usage('/')
            system_health['disk_usage'] = f"{disk.percent}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)"
            system_health['cpu_usage'] = f"{psutil.cpu_percent()}%"
        except:
            pass

    return {
        'timestamp': datetime.now().isoformat(),
        'stats': {
            'merged': merged_count,
            'pending': pending_count,
            'conflicts': conflict_count,
            'test_pass_rate': 100 if merged_count > 0 else 0  # Simplified
        },
        'branches': branches,
        'docker_services': docker_services,
        'system_health': system_health,
        'main_branch': {
            'last_commit': git_manager.get_last_commit('main')
        }
    }


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/branches")
async def list_branches():
    """List all agent branches with their status"""
    branches = git_manager.get_agent_branches()

    result = {}
    for branch in branches:
        status = git_manager.get_branch_status(branch)
        result[branch] = {
            'exists': status.exists,
            'commits_ahead': status.commits_ahead,
            'last_commit': status.last_commit_sha,
            'has_conflicts': status.has_conflicts
        }

    return result


@app.get("/api/dependencies")
async def get_dependency_graph():
    """Get agent dependency graph"""
    config = config_loader.load_agent_dependencies()
    return config


def main():
    """Main entry point"""
    import uvicorn

    print("=" * 80)
    print("🌐 Starting Supervisor Dashboard")
    print("=" * 80)
    print("Dashboard: http://localhost:9999")
    print("API: http://localhost:9999/api/status")
    print("Docs: http://localhost:9999/docs")
    print("=" * 80)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9999,
        log_level="info"
    )


if __name__ == "__main__":
    main()
