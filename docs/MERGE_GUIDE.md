# Merge Conflict Resolution Guide

## 📖 Overview

This guide provides detailed procedures for resolving merge conflicts in the multi-agent development workflow. It covers both automated and manual resolution strategies.

## 🎯 Quick Reference

| Conflict Type | Auto-Resolve | Strategy | Priority |
|---------------|--------------|----------|----------|
| `docker-compose.yml` | ✅ | Merge all services | Critical |
| `requirements.txt` | ✅ | Union & dedupe | High |
| `.env` | ✅ | Merge with namespace | High |
| `configs/ports.yaml` | ❌ | Manual | Critical |
| `*.py` | ❌ | Manual | Medium |
| `*.md` | ✅ | Append both | Low |
| `.gitignore` | ✅ | Union | Low |
| `pytest.ini` | ✅ | Merge sections | Medium |

## 🔧 Resolution Strategies

### 1. Docker Compose Files

**Strategy**: `merge_all_services`

Docker Compose conflicts are common when multiple agents add services. The system automatically merges all service definitions.

**Auto-Resolution Process**:
1. Parse both YAML versions
2. Combine all services
3. Merge volumes and networks
4. Validate with `docker-compose config`

**Manual Override** (if auto-resolution fails):

```bash
# Checkout main version
git checkout main docker-compose.yml

# Manually add missing services from agent branch
git show agent-branch:docker-compose.yml > agent-compose.yml

# Merge services manually
nano docker-compose.yml

# Validate
docker-compose config

# Commit
git add docker-compose.yml
git commit -m "Merge docker-compose from agent-branch"
```

**Common Issues**:
- **Port conflicts**: Two services use same port
  - Solution: Check `configs/agent_dependencies.yaml` for port allocations
  - Update one service to use assigned port

- **Network conflicts**: Services reference different networks
  - Solution: Use shared networks (`inference-network`, `monitoring-network`)

- **Volume name collisions**: Same volume name, different purposes
  - Solution: Prefix volumes with agent name (`agent3-data`, `agent5-cache`)

### 2. Requirements Files

**Strategy**: `union_and_dedupe`

Python dependencies from multiple agents are combined and deduplicated.

**Auto-Resolution Process**:
1. Combine all dependencies
2. Remove duplicates
3. Validate with `pip install --dry-run`

**Version Conflicts**:

If two agents specify different versions:

```text
# Agent 3 wants:
fastapi==0.109.0

# Agent 5 wants:
fastapi==0.110.0
```

**Resolution**:
1. Use highest compatible version
2. Test both agents work with chosen version
3. Update both agents if needed

```bash
# Test with higher version
pip install fastapi==0.110.0
pytest agents/agent3
pytest agents/agent5

# If both pass, use higher version
echo "fastapi==0.110.0" >> requirements.txt
```

### 3. Environment Files

**Strategy**: `merge_with_namespace`

Environment variables are merged with agent-specific prefixes to avoid collisions.

**Auto-Resolution Process**:
1. Parse both .env files
2. Add agent prefix to non-shared variables
3. Keep shared variables (e.g., `NGC_API_KEY`)

**Example**:

```bash
# Before merge - Agent 3 .env
API_PORT=8888
API_HOST=0.0.0.0

# Before merge - Agent 5 .env
API_PORT=8889
API_HOST=0.0.0.0

# After auto-merge
# Shared settings
API_HOST=0.0.0.0

# Agent 3 specific
AGENT3_API_PORT=8888

# Agent 5 specific
AGENT5_API_PORT=8889
```

**Manual Review Required For**:
- Shared secrets (NGC_API_KEY, etc.)
- Database connection strings
- External service URLs

### 4. Port Configuration

**Strategy**: `fail_on_conflict` (Manual resolution required)

Port conflicts MUST be manually resolved to prevent runtime failures.

**Resolution Process**:

1. **Check allocated ports**:
```bash
cat supervisor/configs/agent_dependencies.yaml | grep -A 1 port_allocations
```

2. **Update conflicting service**:
```yaml
# In docker-compose.yml or agent config
ports:
  - "11000:8080"  # Use assigned port from allocation table
```

3. **Update documentation**:
```bash
# Update agent README with new port
echo "Service available at: http://localhost:11000" >> agents/agentX/README.md
```

4. **Validate**:
```bash
docker-compose config
# Check no port duplicates
docker-compose config | grep "published.*:" | sort | uniq -d
```

### 5. Python Source Files

**Strategy**: `git_merge` (Manual resolution with markers)

Python code conflicts require manual review to maintain logic integrity.

**Resolution Process**:

1. **View conflict**:
```bash
git diff --name-only --diff-filter=U
```

2. **Open file and find markers**:
```python
def process_data(self, data):
<<<<<<< HEAD (main)
    # Main branch implementation
    return self.process_v1(data)
=======
    # Agent branch implementation
    return self.process_v2(data)
>>>>>>> agent3-finetuning
```

3. **Resolve based on logic**:

**Option A - Keep both** (if compatible):
```python
def process_data(self, data, version=2):
    if version == 1:
        return self.process_v1(data)
    else:
        return self.process_v2(data)
```

**Option B - Merge logic**:
```python
def process_data(self, data):
    # Combine best of both
    result = self.process_v1(data)
    result = self.enhance_v2(result)
    return result
```

**Option C - Choose one**:
```python
def process_data(self, data):
    # Use agent version (more recent)
    return self.process_v2(data)
```

4. **Test**:
```bash
python -m pytest tests/unit/test_processing.py -v
```

5. **Commit**:
```bash
git add path/to/file.py
git commit -m "Resolve conflict in process_data: merged both implementations"
```

### 6. Documentation Files

**Strategy**: `append_both`

Markdown files are automatically merged by appending both versions.

**Auto-Resolution Process**:
1. Keep content from main branch
2. Append content from agent branch
3. Add separator if needed

**Post-Merge Review**:
- Remove duplicate sections
- Reorganize for clarity
- Update table of contents
- Fix broken links

**Example**:
```bash
# After auto-merge, clean up
nano docs/README.md

# Remove duplicates, reorganize sections
# Commit cleaned version
git add docs/README.md
git commit -m "Clean up merged documentation"
```

## 🚨 Emergency Procedures

### Merge Gone Wrong

If a merge breaks the system:

```bash
# 1. Check current state
git status
git log -1

# 2. Rollback immediately
git reset --hard HEAD~1

# 3. Verify rollback worked
docker-compose config
pytest

# 4. Notify team
# Use supervisor notification system
```

### Tests Failing After Merge

```bash
# 1. View test failures
pytest -v --tb=short

# 2. Identify culprit
git log --oneline -5
git diff HEAD~1..HEAD

# 3. Quick fixes
#    - Revert problematic file
git checkout HEAD~1 -- path/to/problematic_file.py
git commit -m "Revert problematic changes"

#    - Or rollback entire merge
git revert HEAD

# 4. Re-run tests
pytest -v
```

### Conflict in Shared Utilities

**CRITICAL**: Conflicts in `shared/` indicate design issues.

```bash
# 1. DO NOT auto-resolve
# 2. Convene both agent owners
# 3. Review changes together
git diff main..agent-branch -- shared/

# 4. Decide on unified approach
# 5. One agent updates their code to use new shared API
# 6. Merge after coordination
```

## 📋 Conflict Prevention Strategies

### 1. Communication

- Announce changes to shared files in team chat
- Review PRs before merging
- Use draft PRs for work-in-progress

### 2. File Organization

```bash
# Agent-specific files
agents/
  agent1/
    # Only Agent 1 modifies
  agent2/
    # Only Agent 2 modifies

# Shared files (coordinate changes)
shared/
  # Requires team discussion

# Configuration (use separate files)
configs/
  agent1.yaml
  agent2.yaml
```

### 3. Port Management

- Consult `supervisor/configs/agent_dependencies.yaml` before choosing ports
- Request port allocation before implementation
- Update allocation table when using new port

### 4. Regular Syncing

```bash
# Daily sync with main
git checkout agent-branch
git fetch origin main
git merge origin/main

# Resolve conflicts early (when small)
# Commit and push
```

## 🔍 Debugging Conflicts

### View Conflict Details

```bash
# List conflicting files
git diff --name-only --diff-filter=U

# Show conflict with context
git diff HEAD

# Show what changed on each branch
git log --oneline main..agent-branch
git log --oneline agent-branch..main
```

### Understand Why Conflict Occurred

```bash
# When did files diverge?
git merge-base main agent-branch

# What changed on main?
git log $(git merge-base main agent-branch)..main -- path/to/file

# What changed on agent branch?
git log $(git merge-base main agent-branch)..agent-branch -- path/to/file
```

### Test Resolution Before Committing

```bash
# After resolving conflicts
git add .

# Test without committing
pytest
docker-compose config

# If tests pass, commit
git commit -m "Resolve merge conflicts"
```

## 📊 Conflict Metrics

Track conflict resolution effectiveness:

### Key Metrics
- **Conflict Rate**: Conflicts per merge attempt
- **Auto-Resolution Rate**: % conflicts resolved automatically
- **Mean Time to Resolve**: Average time to close conflict
- **Recurring Conflicts**: Same file conflicts multiple times

### Improvement Actions
- High conflict rate → Need better coordination
- Low auto-resolution → Update resolution rules
- Long resolution time → Simplify conflict files
- Recurring conflicts → Refactor shared code

## 🎓 Best Practices

1. **Merge Early, Merge Often**
   - Don't let branches diverge too far
   - Sync with main daily

2. **Small, Focused Changes**
   - Easier to review
   - Simpler conflicts

3. **Test Before Pushing**
   - Run local tests
   - Validate configs
   - Check services start

4. **Document Decisions**
   - Why you chose specific resolution
   - What testing was done
   - Future considerations

5. **Communicate Changes**
   - Announce shared file modifications
   - Update team on breaking changes
   - Review together when uncertain

## 📞 Getting Help

### Automated Help

```bash
# Check conflict resolution rules
cat supervisor/configs/conflict_resolution_rules.yaml

# View dependency graph
cat supervisor/configs/agent_dependencies.yaml

# Get merge recommendations
python supervisor/auto_merge.py --dry-run
```

### Manual Help

1. Post in team chat with:
   - Branch name
   - Conflicting files
   - What you've tried

2. Tag relevant agent owners

3. If urgent, use supervisor notifications

4. Escalate to team lead if blocking multiple agents

---

**Remember**: When in doubt, ask for help. It's better to take 10 minutes to discuss than 2 hours debugging a bad merge.

**Last Updated**: 2025-01-12
