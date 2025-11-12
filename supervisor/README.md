# Supervisor - Multi-Agent Integration System

## 🤖 Overview

The Supervisor is an automated integration system that manages merging work from 10 parallel development agents into the main branch. It handles conflict detection, quality gates, integration testing, and continuous health monitoring.

## 🏗️ Architecture

```
supervisor/
├── auto_merge.py              # Main orchestration - merge automation
├── health_monitor.py           # Continuous service health monitoring
├── dashboard.py                # Real-time web dashboard (FastAPI)
├── conflict_resolver.py        # Automated conflict resolution
├── quality_gates.py            # Code quality, security, docs checks
├── integration_tests.py        # Integration test suite
│
├── utils/
│   ├── gitops.py              # Git operations wrapper
│   ├── config_loader.py       # Configuration management
│   └── notifier.py            # Slack/Discord notifications
│
├── configs/
│   ├── conflict_resolution_rules.yaml
│   └── agent_dependencies.yaml
│
├── requirements.txt
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd supervisor
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Optional: Set up notification webhooks
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"
```

### 3. Start Dashboard

```bash
python dashboard.py
```

Open http://localhost:9999 in your browser to see the real-time integration dashboard.

### 4. Run Manual Merge

```bash
# One-time merge attempt
python auto_merge.py
```

### 5. Start Health Monitor

```bash
# Continuous monitoring (runs in background)
python health_monitor.py --interval 60 &
```

### 6. Set Up Automated Merging

```bash
# Add to crontab for periodic execution
crontab -e

# Run auto-merge every 10 minutes
*/10 * * * * cd /home/user/SparkTest/supervisor && python auto_merge.py >> logs/merge.log 2>&1
```

## 📊 Dashboard Features

The web dashboard (http://localhost:9999) provides:

- **Branch Status**: Real-time view of all agent branches
  - Commits ahead of main
  - Merge conflicts
  - Last commit information

- **Integration Stats**:
  - Branches merged
  - Pending merges
  - Active conflicts
  - Test pass rate

- **Docker Services**: Status of all running containers

- **System Health**: GPU, disk space, CPU usage

- **API Endpoints**:
  - `/api/status` - Full system status (JSON)
  - `/api/branches` - Branch list and status
  - `/api/health` - Simple health check
  - `/docs` - Interactive API documentation

## 🔀 Merge Workflow

The auto-merge system follows this workflow:

1. **Fetch** all remote branches
2. **Order** branches by dependency graph
3. **For each branch**:
   - Check dependencies are merged
   - Check for conflicts
   - Run quality gates
   - Attempt merge
   - Run integration tests
   - Rollback if tests fail
   - Push to remote if successful
4. **Notify** on success/failure

## 🛡️ Quality Gates

Before merging, branches must pass:

### Code Quality
- ✅ Black formatting check
- ✅ Pylint score ≥ 8.0
- ✅ MyPy type hints valid
- ✅ Python syntax valid

### Security
- ✅ Bandit security scan
- ✅ No vulnerable dependencies (Safety)
- ✅ No hardcoded secrets

### Documentation
- ✅ Required docs exist (README.md, etc.)

### Performance
- ✅ Docker images < 5GB
- ✅ docker-compose.yml valid

## 🔧 Conflict Resolution

The system auto-resolves conflicts based on rules in `configs/conflict_resolution_rules.yaml`:

| File Type | Strategy | Auto-Resolve |
|-----------|----------|--------------|
| `docker-compose.yml` | Merge all services | ✅ Yes |
| `requirements.txt` | Union & dedupe | ✅ Yes |
| `.env` | Merge with namespace | ✅ Yes |
| `*.py` | Git merge | ❌ Manual |
| `*.md` | Append both | ✅ Yes |
| `configs/ports.yaml` | Fail | ❌ Manual |

For manual conflicts, the system creates GitHub issues with:
- Diff visualization
- Suggested resolution
- Assigned to agent owner

## 📈 Monitoring & Alerts

The health monitor checks every minute:

- **Docker Services**: Restart failed containers
- **GPU Memory**: Alert if > 95%
- **Disk Space**: Alert if > 90%
- **Zombie Containers**: Auto-cleanup old containers

Alerts are sent via:
- Slack/Discord webhooks
- Console output
- Dashboard notifications

Alert urgency levels:
- 🔥 **CRITICAL**: Service down, tests failing, merge rollback
- ⚠️ **WARNING**: Conflicts, quality gates failed, resource warning
- ℹ️ **INFO**: Successful merge, progress updates

## 🧪 Integration Tests

Three test levels run before merge approval:

### Level 1: Syntax Validation (always)
- Python syntax check
- YAML syntax check
- docker-compose config validation
- Environment variables check

### Level 2: Service Startup (optional)
- All services start without crashing
- Health endpoints respond

### Level 3: End-to-End (optional)
- Complete workflow tests
- Inference pipeline test

Quick mode: `python integration_tests.py --quick` (Level 1 only)

## 📝 Agent Dependencies

Agents are merged in dependency order:

```
Layer 0: agent1-infra (Infrastructure)
         ↓
Layer 1: agent2-dashboard, agent5-inference
         ↓
Layer 2: agent3-finetuning, agent4-advanced
         ↓
Layer 3: agent6-docs, agent7-testing, agent8-deployment
         ↓
Layer 4: agent9-security, agent10-integration
```

Dependencies configured in `configs/agent_dependencies.yaml`.

## 🐛 Troubleshooting

### Merge Fails with Conflicts

```bash
# View conflicting files
git status

# Check conflict resolution rules
cat configs/conflict_resolution_rules.yaml

# Manual resolution
git checkout main
git merge agent-branch-name
# Resolve conflicts
git commit
git push
```

### Quality Gates Fail

```bash
# Run checks locally
cd supervisor
python quality_gates.py

# Fix specific issues
black .  # Format code
pylint --recursive=y .  # Check code quality
mypy .  # Type checking
```

### Dashboard Won't Start

```bash
# Check if port 9999 is available
lsof -i :9999

# Install missing dependencies
pip install -r requirements.txt

# Start with debug logging
uvicorn dashboard:app --host 0.0.0.0 --port 9999 --log-level debug
```

### Health Monitor Issues

```bash
# Check Docker connection
docker ps

# Test GPU access
nvidia-smi

# Start with verbose output
python health_monitor.py --interval 60
```

## 📚 API Reference

### GitOps Manager

```python
from utils.gitops import GitOpsManager

git = GitOpsManager("/path/to/repo")

# Fetch branches
git.fetch_all_branches()

# Get branch status
status = git.get_branch_status("agent1-infra")

# Merge branch
result = git.merge_branch("agent1-infra")

# Rollback if needed
git.rollback_merge()

# Push to remote
git.push_branch("main")
```

### Notifier

```python
from utils.notifier import get_notifier, UrgencyLevel

notifier = get_notifier()

# Send notification
notifier.notify("Message", UrgencyLevel.INFO)

# Convenience methods
notifier.merge_success("branch-name", "commit-sha")
notifier.merge_conflict("branch-name", ["file1", "file2"])
notifier.test_failure("branch-name", ["test1", "test2"])
```

### Conflict Resolver

```python
from conflict_resolver import ConflictResolver

resolver = ConflictResolver()

# Resolve conflicts
results = resolver.resolve_conflicts(["file1.py", "file2.yml"])

# Create issue for manual conflicts
resolver.create_conflict_issue("branch-name", ["file1.py"])
```

## 🔒 Security Considerations

1. **Webhook URLs**: Never commit webhooks to git - use environment variables
2. **GitHub Tokens**: Required for API operations - store securely
3. **Auto-Merge**: Runs with git privileges - ensure proper authentication
4. **Docker Access**: Health monitor needs Docker socket access

## 📊 Performance Metrics

Track these metrics for project health:

- **Merge Velocity**: Time from commit to merge
- **Conflict Rate**: Conflicts per merge attempt
- **Test Pass Rate**: Percentage of merges passing tests
- **Mean Time to Resolve**: Average conflict resolution time

Generate reports:

```bash
# Daily report
python auto_merge.py --report

# View metrics
curl http://localhost:9999/api/status | jq '.stats'
```

## 🤝 Contributing

### Adding New Quality Gates

Edit `quality_gates.py` and add your check:

```python
def check_my_custom_gate(self):
    """My custom quality gate"""
    result = CheckResult(
        name="my_check",
        passed=True,  # Your logic here
        message="Check passed"
    )
    self.checks.append(result)
    return result
```

### Adding Conflict Resolution Strategies

Edit `configs/conflict_resolution_rules.yaml`:

```yaml
path/to/file:
  strategy: custom_strategy
  auto_resolve: true
  validation: "command to validate"
```

Implement strategy in `conflict_resolver.py`.

## 📄 License

Part of the DGX Spark Playbooks project.

## 🙏 Acknowledgments

- GitPython for Git operations
- FastAPI for web dashboard
- Docker SDK for container management

---

**Version**: 1.0.0
**Last Updated**: 2025-01-12
**Maintainer**: DGX Spark Team
