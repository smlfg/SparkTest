# Troubleshooting Guide

Comprehensive troubleshooting guide for Agent 1 Infrastructure issues.

## Quick Diagnostics

Run the validation suite to identify issues:

```bash
cd agents/agent1_infrastructure
./tests/validate_agent1.sh
```

## Common Issues

### SSH Connection Problems

#### Issue: "Permission denied (publickey)"

**Symptoms:**
```bash
$ ssh spark-001
Permission denied (publickey).
```

**Solutions:**

1. **Check SSH key exists:**
```bash
ls -la ~/.ssh/dgx_key
# Should show: -rw------- (600 permissions)
```

2. **Fix permissions:**
```bash
chmod 600 ~/.ssh/dgx_key
chmod 644 ~/.ssh/dgx_key.pub
chmod 700 ~/.ssh
```

3. **Check authorized_keys on remote:**
```bash
ssh -i ~/.ssh/dgx_key user@spark-001 \
  'ls -la ~/.ssh/authorized_keys'
# Should be: -rw------- (600)
```

4. **Re-copy SSH key:**
```bash
./scripts/setup_ssh.sh spark-001
```

#### Issue: "Connection refused"

**Symptoms:**
```bash
$ ssh spark-001
ssh: connect to host spark-001 port 22: Connection refused
```

**Solutions:**

1. **Check SSH service:**
```bash
# On remote node
sudo systemctl status sshd

# Start if not running
sudo systemctl start sshd
sudo systemctl enable sshd
```

2. **Check firewall:**
```bash
# On remote node
sudo ufw status
sudo ufw allow 22/tcp
```

3. **Check SSH listening:**
```bash
# On remote node
sudo netstat -tlnp | grep :22
# Should show sshd listening
```

#### Issue: "Host key verification failed"

**Symptoms:**
```bash
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

**Solutions:**

1. **Remove old key (if expected change):**
```bash
ssh-keygen -R spark-001
ssh-keygen -R 192.168.1.101  # IP address too
```

2. **Or use StrictHostKeyChecking:**
```bash
ssh -o StrictHostKeyChecking=accept-new spark-001
```

### Tailscale VPN Issues

#### Issue: Tailscale not connecting

**Symptoms:**
```bash
$ tailscale status
Tailscale is not running
```

**Solutions:**

1. **Start Tailscale:**
```bash
sudo systemctl start tailscaled
sudo systemctl enable tailscaled
```

2. **Authenticate:**
```bash
sudo tailscale up
# Follow authentication link
```

3. **Check logs:**
```bash
sudo journalctl -u tailscaled -f
```

#### Issue: Can't reach other nodes via Tailscale

**Symptoms:**
```bash
$ ping 100.64.1.2
100% packet loss
```

**Solutions:**

1. **Check Tailscale status:**
```bash
tailscale status
# Verify all nodes are connected
```

2. **Check IP:**
```bash
tailscale ip -4
# Verify you have an IP
```

3. **Test Tailscale ping:**
```bash
tailscale ping spark-001
```

4. **Check routes:**
```bash
tailscale status --json | jq '.Peer[].TailscaleIPs'
```

5. **Restart Tailscale:**
```bash
sudo systemctl restart tailscaled
sudo tailscale up
```

### Student User Management Issues

#### Issue: User creation fails

**Symptoms:**
```bash
$ sudo ./scripts/create_student_users.sh
Error: User creation failed
```

**Solutions:**

1. **Check if user exists:**
```bash
id student01
# If exists, remove first or skip
```

2. **Check quota support:**
```bash
grep usrquota /etc/fstab
# Should show usrquota option
```

3. **Initialize quotas:**
```bash
sudo quotaoff -v /workspace
sudo quotacheck -cugm /workspace
sudo quotaon -v /workspace
```

4. **Check workspace directory:**
```bash
ls -ld /workspace
# Should exist and be writable
sudo mkdir -p /workspace
```

#### Issue: Quota not working

**Symptoms:**
```bash
$ quota -s
quota: Cannot open quotafile //aquota.user: No such file or directory
```

**Solutions:**

1. **Enable quotas in fstab:**
```bash
sudo vim /etc/fstab
# Add usrquota,grpquota to options
# Example:
UUID=xxx  /workspace  ext4  defaults,usrquota,grpquota  0  2
```

2. **Remount filesystem:**
```bash
sudo mount -o remount /workspace
```

3. **Create quota files:**
```bash
sudo quotacheck -cugm /workspace
sudo quotaon -v /workspace
```

4. **Verify quota:**
```bash
sudo repquota -s /workspace
```

#### Issue: Student can't access workspace

**Symptoms:**
```bash
$ ls /workspace/student01
Permission denied
```

**Solutions:**

1. **Check ownership:**
```bash
ls -ld /workspace/student01
# Should be: drwxr-x--- student01 student01
```

2. **Fix ownership:**
```bash
sudo chown -R student01:student01 /workspace/student01
```

3. **Fix permissions:**
```bash
sudo chmod 750 /workspace/student01
sudo chmod 755 /workspace/student01/{datasets,models,checkpoints}
```

### Network Issues

#### Issue: High latency between nodes

**Symptoms:**
```bash
$ ping spark-001
64 bytes from spark-001: icmp_seq=1 ttl=64 time=50.2 ms
```

**Solutions:**

1. **Check network path:**
```bash
traceroute spark-001
# Should be direct, not multi-hop
```

2. **Check MTU:**
```bash
ping -M do -s 8972 spark-001
# Should not fragment
```

3. **Check for congestion:**
```bash
ss -tin | grep cubic
# Look for retransmissions
```

4. **Optimize TCP:**
```bash
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
```

#### Issue: Low bandwidth

**Symptoms:**
```bash
$ iperf3 -c spark-001
[  5]   0.00-10.00  sec   1.00 GBytes   861 Mbits/sec
# Expected: > 9 Gbits/sec on 10GbE
```

**Solutions:**

1. **Check NIC speed:**
```bash
ethtool eth0 | grep Speed
# Should match your hardware
```

2. **Check duplex:**
```bash
ethtool eth0 | grep Duplex
# Should be: Full
```

3. **Check for errors:**
```bash
ifconfig eth0 | grep errors
# Should be 0 or very low
```

4. **Test parallel streams:**
```bash
iperf3 -c spark-001 -P 4
# May improve throughput
```

5. **Check cable/switch:**
```bash
# Physical inspection
# Try different cable/port
```

### GPU/NCCL Issues

#### Issue: NCCL tests fail

**Symptoms:**
```bash
$ /usr/local/bin/nccl_test.sh
NCCL WARN Could not find interface matching ...
```

**Solutions:**

1. **Set correct interface:**
```bash
export NCCL_SOCKET_IFNAME=eth0
/usr/local/bin/nccl_test.sh
```

2. **Disable InfiniBand if not available:**
```bash
export NCCL_IB_DISABLE=1
/usr/local/bin/nccl_test.sh
```

3. **Enable debug:**
```bash
export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=ALL
/usr/local/bin/nccl_test.sh
```

4. **Check NCCL installation:**
```bash
dpkg -l | grep nccl
# Should show libnccl2 installed
```

#### Issue: nvidia-smi not found

**Symptoms:**
```bash
$ nvidia-smi
Command 'nvidia-smi' not found
```

**Solutions:**

1. **Check NVIDIA driver:**
```bash
lsmod | grep nvidia
# Should show nvidia modules
```

2. **Install driver (if needed):**
```bash
# This is Agent 2's responsibility
# For now, verify hardware:
lspci | grep -i nvidia
```

### Ansible Playbook Issues

#### Issue: Playbook fails with "Unreachable"

**Symptoms:**
```bash
$ ansible-playbook playbooks/connect-two-sparks.yaml -i inventory.ini
UNREACHABLE! => {"changed": false, "msg": "Failed to connect"}
```

**Solutions:**

1. **Test connectivity:**
```bash
ansible all -i inventory.ini -m ping
```

2. **Check inventory:**
```bash
cat config/inventory.ini
# Verify hostnames and IPs
```

3. **Check SSH:**
```bash
ansible all -i inventory.ini -m shell -a 'hostname'
```

4. **Increase timeout:**
```bash
ansible-playbook playbooks/connect-two-sparks.yaml \
  -i inventory.ini \
  -e "ansible_ssh_timeout=30"
```

#### Issue: Permission denied during playbook

**Symptoms:**
```bash
FAILED! => {"msg": "Missing sudo password"}
```

**Solutions:**

1. **Add --ask-become-pass:**
```bash
ansible-playbook playbooks/connect-two-sparks.yaml \
  -i inventory.ini \
  --ask-become-pass
```

2. **Or configure passwordless sudo:**
```bash
# On remote nodes
sudo visudo
# Add: username ALL=(ALL) NOPASSWD: ALL
```

### Docker Permission Issues

#### Issue: Student can't use Docker

**Symptoms:**
```bash
$ docker ps
Got permission denied while trying to connect to the Docker daemon socket
```

**Solutions:**

1. **Add user to docker group:**
```bash
sudo usermod -aG docker student01
```

2. **User must log out and back in:**
```bash
# Student needs to logout/login
# Or:
newgrp docker
```

3. **Verify group membership:**
```bash
id student01 | grep docker
# Should show docker in groups
```

4. **Check Docker socket:**
```bash
ls -la /var/run/docker.sock
# Should be: srw-rw---- root docker
```

### Disk Space Issues

#### Issue: Disk full

**Symptoms:**
```bash
$ df -h /workspace
/workspace  50G  50G    0  100% /workspace
```

**Solutions:**

1. **Find large files:**
```bash
sudo du -h /workspace | sort -rh | head -20
```

2. **Check individual quotas:**
```bash
sudo repquota -s /workspace
```

3. **Find old files:**
```bash
find /workspace -type f -mtime +30 -size +1G
```

4. **Clean up:**
```bash
# Students should clean their workspaces
./scripts/manage_student_users.sh info student01
```

## Validation Failures

### Running Full Validation

```bash
cd agents/agent1_infrastructure
./tests/validate_agent1.sh
```

### Common Validation Failures

#### Scripts not executable

**Solution:**
```bash
chmod +x scripts/*.sh
chmod +x tools/*.py
```

#### Configuration files missing

**Solution:**
```bash
cp config/cluster.yaml.example config/cluster.yaml
cp config/inventory.ini.example config/inventory.ini
# Edit with your settings
```

#### Commands not found

**Solutions:**

1. **Install required packages:**
```bash
# Ubuntu/Debian
sudo apt-get install openssh-client openssh-server quota

# Python packages
pip install -r requirements.txt
```

2. **Check PATH:**
```bash
echo $PATH
which ssh
which python3
```

## Logs and Debugging

### SSH Debugging

```bash
# Verbose SSH
ssh -vvv spark-001

# Check SSH logs on server
sudo tail -f /var/log/auth.log
```

### Tailscale Debugging

```bash
# Tailscale logs
sudo journalctl -u tailscaled -f

# Tailscale status
tailscale status --json | jq .
```

### System Logs

```bash
# System messages
sudo tail -f /var/log/syslog

# Kernel messages
sudo dmesg | tail -50

# Service status
systemctl status sshd
systemctl status tailscaled
```

### Network Debugging

```bash
# Check connections
ss -tunap | grep ssh

# Check routes
ip route show

# Check ARP
ip neigh show

# Packet capture
sudo tcpdump -i eth0 port 22 -n
```

## Performance Issues

### Slow SSH connections

**Diagnosis:**
```bash
time ssh spark-001 'exit'
# Should be < 1 second
```

**Solutions:**

1. **Disable DNS lookup:**
```bash
# /etc/ssh/sshd_config
UseDNS no

sudo systemctl restart sshd
```

2. **Use SSH multiplexing:**
```bash
# ~/.ssh/config
ControlMaster auto
ControlPath ~/.ssh/sockets/%r@%h-%p
ControlPersist 600

mkdir -p ~/.ssh/sockets
```

### Slow file transfers

**Diagnosis:**
```bash
# Test with dd
dd if=/dev/zero bs=1M count=1000 | \
  ssh spark-001 'cat > /dev/null'
```

**Solutions:**

1. **Use compression:**
```bash
scp -C large-file spark-001:/tmp/
```

2. **Use rsync:**
```bash
rsync -avz --progress file spark-001:/tmp/
```

3. **Use parallel transfers:**
```bash
# GNU parallel
parallel -j 4 scp file{} spark-001:/tmp/ ::: {1..10}
```

## Getting Help

### Information to Collect

When seeking help, provide:

1. **Error messages:**
```bash
# Full error output
command 2>&1 | tee error.log
```

2. **System information:**
```bash
uname -a
lsb_release -a
```

3. **Network configuration:**
```bash
ip addr show
ip route show
```

4. **Validation results:**
```bash
./tests/validate_agent1.sh > validation.log 2>&1
```

5. **Logs:**
```bash
sudo journalctl -xe > system.log
```

### Support Channels

- **Documentation**: Check README.md files
- **Validation**: Run `./tests/validate_agent1.sh`
- **Logs**: Check system logs
- **Community**: GitHub issues

## Prevention

### Regular Maintenance

1. **Weekly checks:**
```bash
# Disk usage
df -h
sudo repquota -s /workspace

# Failed logins
sudo lastb | head -20

# Network performance
python3 tools/network_validator.py spark-001 spark-002
```

2. **Monthly tasks:**
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade

# Clean old logs
sudo journalctl --vacuum-time=30d

# Audit users
./scripts/manage_student_users.sh list
```

3. **Security audits:**
```bash
# Check failed SSH attempts
sudo grep "Failed password" /var/log/auth.log | tail -20

# Check sudo usage
sudo grep sudo /var/log/auth.log | tail -20

# Review firewall
sudo ufw status verbose
```

### Backup Important Data

```bash
# Backup student data
for user in $(ls /workspace); do
    ./scripts/manage_student_users.sh export "$user" /backup
done

# Backup configurations
tar -czf configs-backup.tar.gz config/ ~/.ssh/
```

### Monitoring

Set up basic monitoring:

```bash
# Disk space alert
echo "df -h | grep -v '^Filesystem' | awk '{if(\$5 > 90) print}'" \
  > /etc/cron.daily/disk-check

# Service health
echo "systemctl is-active sshd tailscaled || mail -s 'Service Down' admin@example.com" \
  > /etc/cron.hourly/service-check
```

---

**Last Updated:** 2025-11-12
**Version:** 1.0.0
