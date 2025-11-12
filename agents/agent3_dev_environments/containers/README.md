# Agent 3: Container Configurations

This directory contains container configurations for development environments.

## Files

### `jax-arm64.Dockerfile`
Dockerfile for JAX optimized container on ARM64 architecture.

**Base Image**: `arm64v8/ubuntu:22.04`

**Installed Packages**:
- Python 3.11
- JAX and JAXlib
- ML frameworks (Optax, Flax, Haiku, Equinox, Diffrax)
- Scientific computing (NumPy, SciPy, Pandas)
- Jupyter Lab
- TensorBoard

**Build**:
```bash
docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:latest .
```

**Run**:
```bash
docker run -it --rm \
  -p 8888:8888 \
  -p 6006:6006 \
  -v $(pwd)/workspace:/workspace \
  agent3/jax-arm64:latest
```

### `jax-entrypoint.sh`
Entrypoint script for JAX container that:
- Shows JAX version and configuration
- Lists available devices
- Runs a test computation
- Launches the main command

### `docker-compose.yml`
Docker Compose configuration for multi-service setup.

**Services**:
- `jax-dev`: Main JAX development environment
- `tensorboard`: TensorBoard visualization service

**Usage**:
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f jax-dev

# Rebuild
docker-compose build
```

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start environment
docker-compose up -d

# Access Jupyter
open http://localhost:8888

# Access TensorBoard
open http://localhost:6006

# Stop environment
docker-compose down
```

### Using Docker Directly

```bash
# Build image
docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:latest .

# Run with Jupyter
docker run -d \
  --name jax-dev \
  -p 8888:8888 \
  -p 6006:6006 \
  -v $(pwd)/workspace:/workspace \
  -e JUPYTER_TOKEN=jaxdev123 \
  agent3/jax-arm64:latest \
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# Run interactive shell
docker run -it --rm \
  -v $(pwd)/workspace:/workspace \
  agent3/jax-arm64:latest \
  bash

# Execute command in running container
docker exec -it jax-dev bash
```

### Using Helper Scripts

```bash
# Launch container (easiest method)
cd ../playbooks
./jax.sh launch

# Stop container
./jax.sh stop

# View logs
./jax.sh logs

# Enter shell
./jax.sh shell
```

## GPU Support

### NVIDIA GPUs on ARM64

Uncomment GPU configuration in `docker-compose.yml`:

```yaml
runtime: nvidia
environment:
  - NVIDIA_VISIBLE_DEVICES=all
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

Or use with Docker run:

```bash
docker run --gpus all \
  -p 8888:8888 \
  agent3/jax-arm64:latest
```

### Apple Silicon (M1/M2/M3)

GPU support on Apple Silicon is automatically configured through Metal Performance Shaders. No additional configuration needed.

## Customization

### Installing Additional Packages

**Method 1**: Modify Dockerfile
```dockerfile
RUN python3 -m pip install --no-cache-dir \
    your-package-here
```

**Method 2**: Install at runtime
```bash
docker exec -it jax-dev pip install your-package
```

**Method 3**: Use requirements.txt
```bash
docker run -v $(pwd)/requirements.txt:/tmp/requirements.txt \
  agent3/jax-arm64:latest \
  pip install -r /tmp/requirements.txt
```

### Changing Python Version

Edit `jax-arm64.Dockerfile`:
```dockerfile
ENV PYTHON_VERSION=3.12
```

Then rebuild:
```bash
docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:latest .
```

### Resource Limits

Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '16'
      memory: 32G
```

## Directories

### `workspace/`
Main working directory mounted as volume. Files here persist across container restarts.

**Usage**:
```bash
# Create workspace
mkdir -p workspace

# Add your code
cp -r ~/my-project workspace/

# Access from container
docker exec -it jax-dev ls /workspace
```

### `notebooks/`
Jupyter notebooks directory mounted at `/workspace/notebooks`.

**Usage**:
```bash
# Create notebooks directory
mkdir -p notebooks

# Add notebook
cp my_notebook.ipynb notebooks/

# Access from Jupyter Lab
# Navigate to http://localhost:8888/lab/tree/notebooks
```

### `logs/`
TensorBoard logs directory.

**Usage**:
```bash
# Create logs directory
mkdir -p logs

# Use in code
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter('/workspace/logs')

# View in TensorBoard
# Navigate to http://localhost:6006
```

## Networking

### Port Mappings

| Container Port | Host Port | Service |
|---------------|-----------|---------|
| 8888 | 8888 | Jupyter Lab |
| 6006 | 6006 | TensorBoard |

### Custom Ports

```bash
docker run -p 9999:8888 agent3/jax-arm64:latest
```

Or in `docker-compose.yml`:
```yaml
ports:
  - "9999:8888"
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs jax-dev-environment

# Check Docker daemon
docker ps
docker info
```

### Permission issues

```bash
# Fix ownership
docker exec -it jax-dev chown -R jaxuser:jaxuser /workspace

# Run as root (not recommended)
docker exec -it -u root jax-dev bash
```

### Out of memory

```bash
# Increase Docker memory limit
# Docker Desktop: Preferences > Resources > Memory

# Or reduce resource usage in code
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.5
```

### JAX not detecting devices

```bash
# Check JAX installation
docker exec -it jax-dev python -c "import jax; print(jax.devices())"

# Check environment variables
docker exec -it jax-dev env | grep JAX

# Reinstall JAX
docker exec -it jax-dev pip install --upgrade jax jaxlib
```

## Performance Optimization

### Build Cache

```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:latest .
```

### Multi-stage Builds

For production, consider multi-stage builds to reduce image size:

```dockerfile
# Builder stage
FROM arm64v8/ubuntu:22.04 AS builder
RUN apt-get update && apt-get install -y build-essential
# ... build dependencies

# Runtime stage
FROM arm64v8/ubuntu:22.04
COPY --from=builder /app /app
# ... runtime only
```

### Layer Caching

Order Dockerfile commands from least to most frequently changing:
1. System packages
2. Python packages
3. Application code

## Security

### Non-root User

Container runs as `jaxuser` by default for security.

```bash
# Switch to root if needed
docker exec -it -u root jax-dev bash
```

### Secrets Management

Use Docker secrets for sensitive data:

```bash
echo "my_password" | docker secret create jupyter_token -
```

## Maintenance

### Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove all (careful!)
docker system prune -a
```

### Updates

```bash
# Pull base image updates
docker pull arm64v8/ubuntu:22.04

# Rebuild container
docker build -f jax-arm64.Dockerfile -t agent3/jax-arm64:latest .

# Restart with new image
docker-compose down
docker-compose up -d
```

## Integration

### With VS Code

Use Dev Containers extension:
1. Open project in VS Code
2. Install "Dev Containers" extension
3. Use `devcontainer.json` in templates
4. Run: "Dev Containers: Reopen in Container"

### With CI/CD

```yaml
# GitHub Actions example
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: agent3/jax-arm64:latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest tests/
```

## See Also

- [Main README](../../README.md)
- [Launch Script](../playbooks/jax.sh)
- [Templates](../templates/README.md)
