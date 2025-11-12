# Student User Management

Complete guide for managing student accounts on the Spark cluster.

## Overview

The student user management system provides tools for creating, managing, and removing student accounts with:

- Automated user creation with workspaces
- Disk quota management
- Resource limits
- SSH key generation
- Secure password management
- Data archiving on removal

## Quick Start

### 1. Create Students

```bash
# Configure students
cd agents/agent1_infrastructure
cp config/students.conf.example config/students.conf
# Edit students.conf with your student list

# Create users
sudo ./scripts/create_student_users.sh

# Or with custom config
sudo ./scripts/create_student_users.sh --config config/students.conf
```

### 2. List Students

```bash
# List all students
./scripts/manage_student_users.sh list

# Show detailed info
./scripts/manage_student_users.sh info student01

# Using Python tool
python3 tools/student_manager.py list
python3 tools/student_manager.py info student01 --format json
```

### 3. Manage Students

```bash
# Update quota
sudo ./scripts/manage_student_users.sh update-quota student01 100G 110G

# Lock/unlock account
sudo ./scripts/manage_student_users.sh lock student01
sudo ./scripts/manage_student_users.sh unlock student01

# Export user data
sudo ./scripts/manage_student_users.sh export student01 /backup
```

### 4. Remove Students

```bash
# Remove with data archive
sudo ./scripts/remove_student_users.sh student01

# Remove without archive
ARCHIVE_DATA=false sudo ./scripts/remove_student_users.sh student01
```

## Configuration

### students.conf

```bash
# List of students
STUDENTS=(
    "student01"
    "student02"
    "student03"
)

# Workspace settings
WORKSPACE_BASE="/workspace"
QUOTA_SOFT="50G"
QUOTA_HARD="55G"

# User settings
DEFAULT_GROUPS="docker,users"
DEFAULT_SHELL="/bin/bash"
SSH_KEY_TYPE="ed25519"
CREATE_SSH_KEYS="true"
```

## Workspace Structure

Each student gets a structured workspace:

```
/workspace/student01/
├── datasets/      # Training datasets
├── models/        # Saved models
├── checkpoints/   # Training checkpoints
├── notebooks/     # Jupyter notebooks
├── scripts/       # Python/bash scripts
└── logs/          # Application logs (private)
```

## Disk Quotas

### View Quota

```bash
# As student
quota -s

# As admin
sudo quota -s -u student01
```

### Set Quota

```bash
# Set custom quota
sudo ./scripts/manage_student_users.sh update-quota student01 100G 110G

# Using Python
sudo python3 tools/student_manager.py quota student01 100G 110G
```

### Quota Limits

Default quotas per student:
- **Soft limit**: 50GB (warning threshold)
- **Hard limit**: 55GB (cannot exceed)

Adjust in `config/students.conf` or per-student.

## SSH Access

### Student SSH Keys

Each student gets an SSH key pair:
- Location: `~/.ssh/id_ed25519`
- Type: Ed25519 (default)
- Public key: `~/.ssh/id_ed25519.pub`

### Access Cluster

Students can SSH between cluster nodes:

```bash
# From student's machine
ssh student01@spark-001

# Between cluster nodes
ssh spark-002
```

## Resource Limits

Default per-student limits:

| Resource | Soft Limit | Hard Limit |
|----------|------------|------------|
| Processes | 1024 | 2048 |
| Open Files | 4096 | 8192 |
| Memory Lock | unlimited | unlimited |

Configured in `/etc/security/limits.d/studentXX.conf`

## User Management Scripts

### create_student_users.sh

Creates student accounts with full setup.

**Usage:**
```bash
sudo ./scripts/create_student_users.sh [options]

Options:
  --config FILE         Configuration file
  --workspace DIR       Workspace base directory
  --quota-soft SIZE     Soft quota limit
  --quota-hard SIZE     Hard quota limit
```

**Features:**
- Creates user accounts
- Generates SSH keys
- Sets up workspace structure
- Configures disk quotas
- Sets resource limits
- Creates welcome message

### manage_student_users.sh

Manage existing student accounts.

**Commands:**
```bash
# List users
./scripts/manage_student_users.sh list

# User info
./scripts/manage_student_users.sh info student01

# Reset password
sudo ./scripts/manage_student_users.sh reset-password student01

# Update quota
sudo ./scripts/manage_student_users.sh update-quota student01 100G 110G

# Lock/unlock
sudo ./scripts/manage_student_users.sh lock student01
sudo ./scripts/manage_student_users.sh unlock student01

# Export data
sudo ./scripts/manage_student_users.sh export student01 /backup
```

### remove_student_users.sh

Safely remove student accounts.

**Usage:**
```bash
sudo ./scripts/remove_student_users.sh student01 [student02 ...]

Environment:
  ARCHIVE_DATA=true/false   Archive before deletion
  ARCHIVE_DIR=/path         Archive directory
  FORCE=true               Skip confirmation
```

**Process:**
1. Kills user processes
2. Archives workspace data (optional)
3. Removes workspace
4. Removes quota
5. Deletes user account

## Python Management Tool

### student_manager.py

Advanced Python interface for user management.

**Usage:**
```bash
# List students
python3 tools/student_manager.py list [--format json|csv|table]

# Get info
python3 tools/student_manager.py info student01

# Create from config
sudo python3 tools/student_manager.py create --config students.conf

# Remove user
sudo python3 tools/student_manager.py remove student01 [--no-archive]

# Update quota
sudo python3 tools/student_manager.py quota student01 100G 110G

# Lock/unlock
sudo python3 tools/student_manager.py lock student01
sudo python3 tools/student_manager.py unlock student01

# Generate report
python3 tools/student_manager.py report --output report.json
```

**Output Formats:**
- **table**: Human-readable table
- **json**: JSON format for scripting
- **csv**: CSV for spreadsheets

## Ansible Playbook

### manage-student-users.yaml

Deploy student accounts across entire cluster.

**Usage:**
```bash
ansible-playbook playbooks/manage-student-users.yaml -i inventory.ini

# Custom variables
ansible-playbook playbooks/manage-student-users.yaml -i inventory.ini \
  -e "workspace_base=/data/students" \
  -e "quota_soft=100G" \
  -e "quota_hard=110G"
```

**Features:**
- Multi-node deployment
- Consistent setup across cluster
- Automatic SSH key distribution
- Quota configuration
- Resource limits

## Passwords

### Initial Password

Default password: `spark<YEAR>` (e.g., `spark2025`)

Students **must** change password on first login.

### Reset Password

```bash
sudo ./scripts/manage_student_users.sh reset-password student01
```

Generates random temporary password that must be changed.

## Security

### Best Practices

1. **Use SSH keys** for authentication
2. **Disable password auth** after SSH keys are set up
3. **Audit user actions** regularly
4. **Monitor disk usage** to prevent quota violations
5. **Lock inactive accounts** after semester ends
6. **Archive data** before removing users

### Audit Commands

```bash
# Check last logins
last -n 20

# Check running processes
ps aux | grep student

# Check disk usage
du -sh /workspace/*

# Check quota usage
sudo repquota -s /workspace
```

## Troubleshooting

### Quota Not Working

```bash
# Check if quotas enabled
grep usrquota /etc/fstab

# Enable quotas
sudo vim /etc/fstab  # Add usrquota,grpquota
sudo mount -o remount /workspace
sudo quotacheck -cugm /workspace
sudo quotaon -v /workspace
```

### User Cannot Login

```bash
# Check if account locked
sudo passwd -S student01

# Unlock account
sudo passwd -u student01

# Check SSH key
sudo -u student01 ssh-keygen -l -f /home/student01/.ssh/id_ed25519
```

### Workspace Permission Issues

```bash
# Fix ownership
sudo chown -R student01:student01 /workspace/student01

# Fix permissions
sudo chmod 750 /workspace/student01
sudo chmod 755 /workspace/student01/{datasets,models,checkpoints}
sudo chmod 700 /workspace/student01/logs
```

## Integration with Agent1 Output

Access student information programmatically:

```python
from agents.agent1_infrastructure.agent1_output import get_student_info

# Get student configuration
student_info = get_student_info()

print(f"Students configured: {len(student_info['config']['students'])}")
print(f"Workspace base: {student_info['config']['workspace_base']}")
print(f"Quota: {student_info['config']['quota_soft']}")

# List active users
for user in student_info['users']:
    print(f"User: {user['username']} - Workspace: {user['workspace']}")
```

## Bulk Operations

### Create Multiple Users

```bash
# From config file
sudo ./scripts/create_student_users.sh --config students.conf
```

### Remove Multiple Users

```bash
# List of users
sudo ./scripts/remove_student_users.sh student01 student02 student03

# Or with loop
for user in student{01..10}; do
    sudo ./scripts/remove_student_users.sh "$user"
done
```

### Update All Quotas

```bash
# Bash script
for user in $(ls /workspace); do
    sudo ./scripts/manage_student_users.sh update-quota "$user" 100G 110G
done
```

## Reporting

### Generate Report

```bash
# Python tool
python3 tools/student_manager.py report --output report.json

# View report
cat report.json | jq .
```

**Report includes:**
- Total student count
- Per-user statistics
- Quota usage
- Workspace sizes
- System information

## Maintenance

### Regular Tasks

1. **Weekly:** Check quota usage
2. **Monthly:** Audit inactive accounts
3. **Semester end:** Archive and remove old accounts
4. **Quarterly:** Review resource limits

### Cleanup Old Accounts

```bash
# Find inactive users (no login in 90 days)
lastlog -b 90 | grep student

# Lock inactive accounts
for user in $(lastlog -b 90 | grep student | awk '{print $1}'); do
    sudo ./scripts/manage_student_users.sh lock "$user"
done

# Archive and remove after semester
for user in student{01..10}; do
    ARCHIVE_DATA=true sudo ./scripts/remove_student_users.sh "$user"
done
```

## Support

For issues:
- Check logs in `/var/log/auth.log`
- Review quota with `quota -s`
- Check workspace permissions
- Verify SSH keys

Admin contact: cluster-admin@example.com

---

**Last Updated:** 2025-11-12
**Version:** 1.0.0
