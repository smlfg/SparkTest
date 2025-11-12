#!/bin/bash
# JAX Container Management Script
# Simple interface for launching and managing JAX containers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_DIR="$(cd "$SCRIPT_DIR/../containers" && pwd)"
JAX_CONTAINER_NAME="${JAX_CONTAINER_NAME:-jax-dev-environment}"
JAX_IMAGE="${JAX_IMAGE:-agent3/jax-arm64:latest}"
JUPYTER_PORT="${JUPYTER_PORT:-8888}"
TENSORBOARD_PORT="${TENSORBOARD_PORT:-6006}"

echo "========================================="
echo "JAX ARM64 Container Management"
echo "========================================="

# Function to launch JAX container
launch_jax_container() {
    local gpus="${1:-all}"

    echo "[1/4] Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        echo "ERROR: Docker is not installed!"
        exit 1
    fi

    echo "[2/4] Creating workspace directories..."
    mkdir -p "$CONTAINER_DIR/workspace"
    mkdir -p "$CONTAINER_DIR/notebooks"
    mkdir -p "$CONTAINER_DIR/logs"

    echo "[3/4] Building JAX container image..."
    cd "$CONTAINER_DIR"

    # Copy entrypoint script if building standalone
    if [ ! -f "$CONTAINER_DIR/jax-entrypoint.sh" ]; then
        cp "$SCRIPT_DIR/jax-entrypoint.sh" "$CONTAINER_DIR/" 2>/dev/null || true
    fi

    docker build -f jax-arm64.Dockerfile -t "$JAX_IMAGE" .

    echo "[4/4] Launching JAX container..."

    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${JAX_CONTAINER_NAME}$"; then
        echo "Container $JAX_CONTAINER_NAME already exists. Stopping and removing..."
        docker stop "$JAX_CONTAINER_NAME" 2>/dev/null || true
        docker rm "$JAX_CONTAINER_NAME" 2>/dev/null || true
    fi

    # Build docker run command
    DOCKER_CMD="docker run -d \
        --name $JAX_CONTAINER_NAME \
        --hostname jax-dev \
        -p $JUPYTER_PORT:8888 \
        -p $TENSORBOARD_PORT:6006 \
        -v $CONTAINER_DIR/workspace:/workspace \
        -v $CONTAINER_DIR/notebooks:/workspace/notebooks \
        -e JAX_PLATFORM_NAME=cpu \
        -e XLA_FLAGS=--xla_force_host_platform_device_count=8 \
        -e JAX_ENABLE_X64=True \
        -e JUPYTER_TOKEN=jaxdev123"

    # Add GPU support if requested and available
    if [ "$gpus" != "none" ] && [ -x "$(command -v nvidia-smi)" ]; then
        echo "Enabling GPU support..."
        DOCKER_CMD="$DOCKER_CMD --gpus $gpus"
    fi

    # Complete the command
    DOCKER_CMD="$DOCKER_CMD $JAX_IMAGE jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"

    # Execute docker run
    eval $DOCKER_CMD

    echo ""
    echo "========================================="
    echo "JAX Container launched successfully!"
    echo "========================================="
    echo "Jupyter Lab: http://localhost:$JUPYTER_PORT"
    echo "Token: jaxdev123"
    echo "TensorBoard: http://localhost:$TENSORBOARD_PORT"
    echo "Container: $JAX_CONTAINER_NAME"
    echo ""
    echo "Useful commands:"
    echo "  docker exec -it $JAX_CONTAINER_NAME bash"
    echo "  docker logs $JAX_CONTAINER_NAME"
    echo "  docker stop $JAX_CONTAINER_NAME"
    echo "========================================="
}

# Function to stop container
stop_jax_container() {
    echo "Stopping JAX container..."
    docker stop "$JAX_CONTAINER_NAME"
}

# Function to restart container
restart_jax_container() {
    echo "Restarting JAX container..."
    docker restart "$JAX_CONTAINER_NAME"
}

# Function to show logs
show_jax_logs() {
    docker logs -f "$JAX_CONTAINER_NAME"
}

# Function to enter container shell
enter_jax_shell() {
    docker exec -it "$JAX_CONTAINER_NAME" bash
}

# Export functions
export -f launch_jax_container
export -f stop_jax_container
export -f restart_jax_container
export -f show_jax_logs
export -f enter_jax_shell

# Handle command line arguments
case "${1:-launch}" in
    launch|start)
        launch_jax_container "${2:-all}"
        ;;
    stop)
        stop_jax_container
        ;;
    restart)
        restart_jax_container
        ;;
    logs)
        show_jax_logs
        ;;
    shell|bash|exec)
        enter_jax_shell
        ;;
    *)
        echo "Usage: $0 {launch|start|stop|restart|logs|shell} [gpus]"
        echo ""
        echo "Commands:"
        echo "  launch, start  - Build and launch JAX container (default)"
        echo "  stop           - Stop running container"
        echo "  restart        - Restart container"
        echo "  logs           - Show container logs"
        echo "  shell          - Enter container shell"
        echo ""
        echo "GPU Options (for launch):"
        echo "  all   - Use all available GPUs (default)"
        echo "  none  - CPU only"
        echo "  0,1   - Specific GPU indices"
        exit 1
        ;;
esac
