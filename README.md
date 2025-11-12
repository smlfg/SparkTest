# Agent 3: Development Environments

**Scope**: IDEs + Coding Tools

A comprehensive development environment setup system featuring VS Code remote server, optimized JAX ARM64 container, and multiple language development templates.

## Features

### 🚀 Core Deliverables

1. **VS Code Remote Server** - Cloud-based IDE accessible from anywhere
2. **JAX ARM64 Container** - Optimized machine learning environment for ARM64
3. **Dev Environment Templates** - Pre-configured setups for Python, Rust, Go, and C++
4. **Code Launch Scripts** - Automated setup and management tools

### 📦 Playbooks

- **vscode** - Remote development server setup
- **jax** - Optimized JAX environment with GPU support

## Quick Start

### Prerequisites

- **Required**: Docker (for JAX container)
- **Optional**: Ansible (for playbook-based setup)
- **Recommended**: 8GB+ RAM, multi-core CPU

### Installation

```bash
# Clone and navigate to repository
cd SparkTest

# Make launch script executable
chmod +x agent3_launch.sh

# Setup complete environment (VS Code + JAX)
./agent3_launch.sh all
```

## Usage

### Basic Commands

```bash
# Setup complete environment
./agent3_launch.sh all

# Start VS Code Server only
./agent3_launch.sh vscode

# Launch JAX container only
./agent3_launch.sh jax

# Check environment status
./agent3_launch.sh status

# Stop JAX container
./agent3_launch.sh stop-jax

# List available templates
./agent3_launch.sh templates
```

### Interface Output Example

```bash
# agent3_launch.sh
start_vscode_server --port 8443
launch_jax_container --gpus all
```

### Advanced Usage

```bash
# Custom VS Code port
./agent3_launch.sh vscode --port 9000

# JAX with specific GPUs
./agent3_launch.sh jax --gpus 0,1

# Use Ansible playbooks
./agent3_launch.sh all --ansible
```

### Using Environment Templates

```bash
# Python Machine Learning
source agent3/templates/python-ml.env
./agent3_launch.sh jax

# Rust Development
source agent3/templates/rust-dev.env

# Go Development
source agent3/templates/go-dev.env

# C++ Development
source agent3/templates/cpp-dev.env
```

## Components

### 1. VS Code Remote Server

Cloud-based VS Code accessible via web browser.

**Features:**
- Web-based IDE
- Extension support
- Multi-language support
- Persistent sessions

**Access:**
- URL: `http://localhost:8443`
- Default Password: `changeme123`

**Configuration:**
```bash
export VSCODE_PORT=8443
export VSCODE_PASSWORD=your_password
./agent3_launch.sh vscode
```

### 2. JAX ARM64 Container

Optimized container for machine learning with JAX on ARM64 architecture.

**Features:**
- JAX with CPU/GPU support
- Jupyter Lab integration
- TensorBoard support
- Scientific computing stack (NumPy, SciPy, Pandas)
- ML frameworks (Optax, Flax, Haiku)

**Access:**
- Jupyter Lab: `http://localhost:8888` (token: `jaxdev123`)
- TensorBoard: `http://localhost:6006`

**Container Management:**
```bash
# Launch container
./agent3_launch.sh jax --gpus all

# Stop container
./agent3_launch.sh stop-jax

# View logs
docker logs jax-dev-environment

# Enter container shell
docker exec -it jax-dev-environment bash
```

### 3. Development Templates

Pre-configured environment files for different languages:

| Template | Language | Key Features |
|----------|----------|--------------|
| `python-ml.env` | Python 3.11 | JAX, Jupyter, TensorBoard |
| `rust-dev.env` | Rust | ARM64 cross-compilation, Clippy |
| `go-dev.env` | Go | Modules, ARM64, race detection |
| `cpp-dev.env` | C++20 | CMake, Clang, sanitizers |
| `devcontainer.json` | Multi | VS Code Dev Containers |

**Template Usage:**
```bash
# Source a template
source agent3/templates/python-ml.env

# Verify activation
echo $PROJECT_NAME
echo $PYTHON_VERSION
```

### 4. Launch Scripts

#### Main Launch Script: `agent3_launch.sh`

Central orchestration script for all Agent 3 services.

**Commands:**
- `all/setup` - Complete environment setup
- `vscode/code` - VS Code Server only
- `jax` - JAX container only
- `stop-jax` - Stop JAX container
- `status` - Environment status
- `templates` - List templates
- `help` - Show help

#### Playbook Scripts

Located in `agent3/playbooks/`:

| Script | Purpose | Type |
|--------|---------|------|
| `vscode.yml` | VS Code setup | Ansible |
| `vscode.sh` | VS Code setup | Shell |
| `jax.yml` | JAX container | Ansible |
| `jax.sh` | JAX container | Shell |

## Project Structure

```
SparkTest/
├── agent3_launch.sh              # Main launch script
├── agent3/
│   ├── playbooks/                # Automation playbooks
│   │   ├── vscode.yml           # VS Code Ansible playbook
│   │   ├── vscode.sh            # VS Code shell script
│   │   ├── jax.yml              # JAX Ansible playbook
│   │   └── jax.sh               # JAX shell script
│   ├── containers/               # Container configurations
│   │   ├── jax-arm64.Dockerfile # JAX container image
│   │   ├── jax-entrypoint.sh    # JAX container entrypoint
│   │   └── docker-compose.yml   # Docker Compose config
│   ├── templates/                # Environment templates
│   │   ├── python-ml.env        # Python ML template
│   │   ├── rust-dev.env         # Rust template
│   │   ├── go-dev.env           # Go template
│   │   ├── cpp-dev.env          # C++ template
│   │   ├── devcontainer.json    # VS Code Dev Container
│   │   └── README.md            # Templates documentation
│   └── scripts/                  # Utility scripts
└── README.md                     # This file
```

## Dependencies

### Required
- **Docker** - Container runtime for JAX environment

### Optional
- **Ansible** - For playbook-based automation
- **code-server** - Installed automatically by scripts

### System Requirements
- OS: Linux (tested on Ubuntu 22.04), macOS (ARM64)
- RAM: 8GB minimum, 16GB recommended
- CPU: Multi-core recommended (4+ cores)
- Disk: 10GB free space

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VSCODE_PORT` | VS Code Server port | `8443` |
| `VSCODE_PASSWORD` | VS Code password | `changeme123` |
| `JAX_GPU` | GPU configuration | `all` |
| `USE_ANSIBLE` | Use Ansible playbooks | `false` |

### Configuration Files

- **VS Code**: `~/.config/code-server/config.yaml`
- **JAX Container**: `agent3/containers/docker-compose.yml`
- **Templates**: `agent3/templates/*.env`

## Integration with Other Agents

### Dependencies

- **Agent 1 (SSH)** - Remote access to development environments
- **Agent 2 (Dashboard)** - Monitoring and status visualization

### Interfaces

Export functions for programmatic access:

```bash
source agent3_launch.sh

# Use exported functions
start_vscode_server 8443
launch_jax_container all
show_status
```

## Troubleshooting

### VS Code Server Issues

```bash
# Check if code-server is installed
which code-server

# Check if running
pgrep -f code-server

# View logs
journalctl -u code-server -f

# Restart
systemctl restart code-server
```

### JAX Container Issues

```bash
# Check Docker status
docker ps -a

# View container logs
docker logs jax-dev-environment

# Restart container
docker restart jax-dev-environment

# Rebuild container
cd agent3/containers
docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:latest .
```

### Port Conflicts

```bash
# Check port usage
lsof -i :8443
lsof -i :8888

# Use different ports
./agent3_launch.sh vscode --port 9000
export JUPYTER_PORT=9999
```

### Permission Issues

```bash
# Make scripts executable
chmod +x agent3_launch.sh
chmod +x agent3/playbooks/*.sh
chmod +x agent3/containers/*.sh
```

## Development

### Adding New Templates

1. Create new template file in `agent3/templates/`
2. Follow existing template format
3. Update `agent3/templates/README.md`
4. Test with `agent3_launch.sh`

### Modifying Containers

1. Edit `agent3/containers/jax-arm64.Dockerfile`
2. Rebuild: `docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:latest .`
3. Test: `./agent3_launch.sh jax`

### Testing

```bash
# Test VS Code setup
./agent3_launch.sh vscode
curl http://localhost:8443

# Test JAX container
./agent3_launch.sh jax
docker exec -it jax-dev-environment python -c "import jax; print(jax.__version__)"

# Test templates
source agent3/templates/python-ml.env
echo $JAX_PLATFORM_NAME
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review troubleshooting section

## Changelog

### v1.0.0 (Initial Release)
- VS Code remote server with Ansible/shell setup
- JAX ARM64 container with Jupyter integration
- Development templates for Python, Rust, Go, C++
- Unified launch script with status monitoring
- Docker Compose configuration
- Comprehensive documentation

## Roadmap

- [ ] GPU optimization for JAX on ARM64
- [ ] Additional language templates (Java, TypeScript, etc.)
- [ ] CI/CD integration templates
- [ ] Remote development over SSH
- [ ] Multi-node JAX cluster support
- [ ] Monitoring and metrics dashboard
- [ ] Automated backups and snapshots

---

**Agent 3: Development Environments** - Making world-class development environments accessible and easy to deploy.
