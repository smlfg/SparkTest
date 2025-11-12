# Network Setup Guide

Complete guide for configuring network infrastructure for Spark cluster.

## Overview

Agent 1 provides multiple network configuration options:
- **SSH**: Secure shell access for cluster management
- **Tailscale VPN**: Optional secure overlay network
- **Multi-node Networking**: Direct node-to-node communication
- **NCCL**: High-performance multi-GPU networking

## SSH Configuration

### Quick Setup

```bash
# Generate SSH keys and configure access
cd agents/agent1_infrastructure
./scripts/setup_ssh.sh spark-001 spark-002
```

### Manual Setup

#### 1. Generate SSH Key

```bash
# Generate Ed25519 key (recommended)
ssh-keygen -t ed25519 -f ~/.ssh/dgx_key -N "" -C "spark-cluster"

# Or RSA if Ed25519 not supported
ssh-keygen -t rsa -b 4096 -f ~/.ssh/dgx_key -N "" -C "spark-cluster"
```

#### 2. Copy Key to Nodes

```bash
# Copy to each node
ssh-copy-id -i ~/.ssh/dgx_key user@spark-001
ssh-copy-id -i ~/.ssh/dgx_key user@spark-002
```

#### 3. Configure SSH Client

Add to `~/.ssh/config`:

```ssh-config
Host spark-* dgx-*
    IdentityFile ~/.ssh/dgx_key
    User your-username
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60
    ServerAliveCountMax 3
    Compression yes
```

#### 4. Test Connection

```bash
# Test SSH access
ssh spark-001 hostname

# Test without password
ssh -o BatchMode=yes spark-001 "echo 'SSH OK'"
```

### SSH Server Configuration

#### Security Hardening

Edit `/etc/ssh/sshd_config`:

```ssh-config
# Disable password authentication
PasswordAuthentication no

# Enable public key authentication
PubkeyAuthentication yes

# Disable root login
PermitRootLogin no

# Enable X11 forwarding (optional)
X11Forwarding yes

# Set keep-alive
ClientAliveInterval 60
ClientAliveCountMax 3
```

Restart SSH:

```bash
sudo systemctl restart sshd
```

## Tailscale VPN Setup

### Prerequisites

- Tailscale account: https://login.tailscale.com
- Auth key: https://login.tailscale.com/admin/settings/keys

### Installation

```bash
# Run setup script
cd agents/agent1_infrastructure
./scripts/setup_tailscale.sh <auth-key> spark-001

# Or use Ansible playbook
ansible-playbook playbooks/tailscale.yaml -i inventory.ini \
  --extra-vars "tailscale_auth_key=<your-key>"
```

### Manual Installation

#### 1. Install Tailscale

**Ubuntu/Debian:**
```bash
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.noarmor.gpg | \
  sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null

curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.tailscale-keyring.list | \
  sudo tee /etc/apt/sources.list.d/tailscale.list

sudo apt-get update
sudo apt-get install tailscale
```

**RHEL/CentOS:**
```bash
sudo dnf config-manager --add-repo \
  https://pkgs.tailscale.com/stable/rhel/8/tailscale.repo
sudo dnf install tailscale
```

#### 2. Connect to Tailscale

```bash
# Start Tailscale
sudo systemctl enable --now tailscaled

# Connect with auth key
sudo tailscale up --authkey=<your-auth-key> --hostname=spark-001

# Or authenticate via browser
sudo tailscale up --hostname=spark-001
```

#### 3. Get Tailscale IP

```bash
# Get your Tailscale IP
tailscale ip -4

# Example: 100.64.1.2
```

#### 4. Test Connectivity

```bash
# From another Tailscale node
ping 100.64.1.2

# SSH via Tailscale
ssh user@100.64.1.2
```

### Subnet Router (Optional)

Make a node act as subnet router:

```bash
# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1

# Make permanent
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv6.conf.all.forwarding=1" | sudo tee -a /etc/sysctl.conf

# Advertise routes
sudo tailscale up --advertise-routes=192.168.1.0/24 --accept-routes
```

Approve routes in Tailscale admin console.

## Multi-Node Cluster Networking

### Single Node Setup

```bash
ansible-playbook playbooks/connect-to-your-spark.yaml -i inventory.ini
```

### Two-Node Cluster

```bash
ansible-playbook playbooks/connect-two-sparks.yaml -i inventory.ini
```

### Configuration

Edit `config/cluster.yaml`:

```yaml
cluster_name: spark-cluster
nodes:
  - hostname: spark-001
    ip: 192.168.1.101
    user: ubuntu
  - hostname: spark-002
    ip: 192.168.1.102
    user: ubuntu

ssh_key_path: ~/.ssh/dgx_key
```

### Network Requirements

- **Ports**:
  - 22: SSH
  - 6006: TensorBoard (optional)
  - 8888: Jupyter (optional)
  - Custom: Application-specific

- **Bandwidth**:
  - Minimum: 1 Gbps
  - Recommended: 10 Gbps
  - Optimal: 25+ Gbps with InfiniBand

## NCCL Multi-GPU Networking

For distributed GPU training.

### Setup

```bash
ansible-playbook playbooks/nccl.yaml -i inventory.ini
```

### Network Interface Selection

NCCL automatically detects, but can be configured:

```bash
# Set network interface
export NCCL_SOCKET_IFNAME=eth0,eth1

# For InfiniBand
export NCCL_IB_HCA=mlx5
```

### InfiniBand Configuration

If you have InfiniBand:

```bash
# Check IB status
ibstat

# Install tools
sudo apt-get install infiniband-diags ibverbs-utils

# Test IB performance
ib_write_bw -d mlx5_0 -a
```

### Test NCCL

```bash
# Single node test
sudo /usr/local/bin/nccl_test.sh

# Multi-node test
sudo /usr/local/bin/nccl_multinode_test.sh
```

## Network Validation

### Automated Validation

```bash
# Run network validator
python3 tools/network_validator.py spark-001 spark-002 \
  --tests ssh ping bandwidth gpu \
  --output validation.json
```

### Manual Tests

#### SSH Connectivity

```bash
# Test SSH to each node
for node in spark-001 spark-002; do
    ssh -o BatchMode=yes $node "echo OK" || echo "FAIL: $node"
done
```

#### Network Latency

```bash
# Ping test
ping -c 10 spark-001

# Expected: < 1ms for local network
```

#### Network Bandwidth

```bash
# Start iperf3 server on target
ssh spark-001 'iperf3 -s -D'

# Run client
iperf3 -c spark-001 -t 10

# Expected: > 1 Gbps
```

#### GPU Communication

```bash
# Check GPU topology
nvidia-smi topo -m

# Test NCCL bandwidth
/opt/nccl-tests/build/all_reduce_perf -b 8 -e 256M -f 2
```

## Network Troubleshooting

### SSH Issues

**Cannot connect:**
```bash
# Check SSH service
sudo systemctl status sshd

# Check SSH port
sudo netstat -tlnp | grep :22

# Check firewall
sudo ufw status
```

**Permission denied:**
```bash
# Check key permissions
chmod 600 ~/.ssh/dgx_key
chmod 644 ~/.ssh/dgx_key.pub

# Check authorized_keys
ls -la ~/.ssh/authorized_keys  # Should be 600
```

### Tailscale Issues

**Not connecting:**
```bash
# Check Tailscale status
tailscale status

# Check logs
sudo journalctl -u tailscaled -f

# Restart Tailscale
sudo systemctl restart tailscaled
sudo tailscale up
```

**Can't reach nodes:**
```bash
# Check Tailscale IPs
tailscale ip -4

# Check routes
tailscale status --json | jq '.Peer[].TailscaleIPs'

# Verify connectivity
tailscale ping <node-name>
```

### Network Performance

**Low bandwidth:**
```bash
# Check NIC speed
ethtool eth0 | grep Speed

# Check for errors
ifconfig eth0 | grep errors

# Test with iperf3
iperf3 -c <target> -P 4  # Parallel streams
```

**High latency:**
```bash
# Check MTU
ip link show | grep mtu

# Check congestion
ss -tin | grep cubic

# Check routing
traceroute spark-001
```

### NCCL Issues

**NCCL errors:**
```bash
# Enable debug
export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=ALL

# Test
/usr/local/bin/nccl_test.sh
```

**Network not detected:**
```bash
# Check interface
export NCCL_SOCKET_IFNAME=eth0

# Disable IB if not available
export NCCL_IB_DISABLE=1
```

## Network Security

### Firewall Configuration

**Allow cluster traffic:**
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow from cluster subnet
sudo ufw allow from 192.168.1.0/24

# Enable firewall
sudo ufw enable
```

### Fail2ban (Optional)

Protect against brute force:

```bash
# Install
sudo apt-get install fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo vim /etc/fail2ban/jail.local

# Enable SSH jail
[sshd]
enabled = true
maxretry = 3
bantime = 3600

# Restart
sudo systemctl restart fail2ban
```

### Network Monitoring

```bash
# Monitor connections
watch -n 1 'ss -tunap | grep ssh'

# Monitor bandwidth
nethogs

# Monitor latency
mtr spark-001
```

## Best Practices

1. **Use SSH keys** instead of passwords
2. **Disable root SSH** login
3. **Use Tailscale** for secure remote access
4. **Configure firewall** properly
5. **Monitor network** performance regularly
6. **Use InfiniBand** for GPU clusters if available
7. **Test failover** scenarios
8. **Document** network topology
9. **Keep software updated**
10. **Audit access** regularly

## Integration

### Export Network Configuration

```python
from agents.agent1_infrastructure.agent1_output import get_connection_info

conn = get_connection_info()
print(f"SSH Key: {conn['ssh']['key_path']}")
print(f"Nodes: {conn['network']['nodes']}")
print(f"Tailscale: {conn['network']['tailscale_enabled']}")
```

### Use in Scripts

```bash
# Source configuration
eval $(python3 agent1_output.py ssh | jq -r 'to_entries[] | "\(.key | ascii_upcase)=\(.value)"')

# Use in SSH commands
ssh -i "$KEY_PATH" "$USER@spark-001"
```

## Performance Optimization

### TCP Tuning

```bash
# Increase buffer sizes
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 67108864"
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 67108864"

# Enable TCP BBR
sudo sysctl -w net.core.default_qdisc=fq
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
```

### MTU Optimization

```bash
# Find optimal MTU
tracepath spark-001

# Set MTU
sudo ip link set dev eth0 mtu 9000  # Jumbo frames
```

---

**Last Updated:** 2025-11-12
**Version:** 1.0.0
