# Shared Base Docker Image for All Agents
# Base: NVIDIA PyTorch with CUDA support
FROM nvcr.io/nvidia/pytorch:24.10-py3

LABEL maintainer="DGX Spark Playbooks"
LABEL description="Shared base image for all agents with GPU support"
LABEL version="1.0.0"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Install NVIDIA Container Toolkit and CUDA Toolkit
RUN apt-get update && apt-get install -y --no-install-recommends \
    nvidia-container-toolkit \
    cuda-toolkit-12-0 \
    # Build essentials
    build-essential \
    cmake \
    ninja-build \
    git \
    curl \
    wget \
    ca-certificates \
    # System utilities
    vim \
    nano \
    htop \
    tmux \
    screen \
    # Network utilities
    net-tools \
    iputils-ping \
    dnsutils \
    netcat \
    # Development tools
    pkg-config \
    gdb \
    valgrind \
    # Compression tools
    zip \
    unzip \
    bzip2 \
    # Additional libraries
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python packages
RUN python -m pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    wheel

# Install shared Python dependencies
RUN python -m pip install --no-cache-dir \
    # Web frameworks
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    requests>=2.31.0 \
    aiohttp>=3.9.0 \
    # Data processing
    numpy>=1.24.0 \
    pandas>=2.0.0 \
    # Serialization
    pyyaml>=6.0 \
    toml>=0.10.2 \
    # Validation
    pydantic>=2.5.0 \
    jsonschema>=4.20.0 \
    # CLI tools
    click>=8.1.7 \
    rich>=13.7.0 \
    # Logging and monitoring
    loguru>=0.7.2 \
    prometheus-client>=0.19.0 \
    # Testing
    pytest>=7.4.0 \
    pytest-asyncio>=0.21.0 \
    pytest-cov>=4.1.0 \
    # Type checking
    mypy>=1.7.0 \
    # Linting
    ruff>=0.1.6

# Create shared directories
RUN mkdir -p /app/shared \
    /app/config \
    /app/logs \
    /app/data \
    /workspace

# Copy shared utilities (will be mounted or copied by specific agents)
WORKDIR /app

# Create non-root user for security
RUN useradd -m -s /bin/bash -u 1000 agent && \
    chown -R agent:agent /app /workspace

# Health check dependencies
RUN python -m pip install --no-cache-dir \
    httpx>=0.25.0

# Set default user
USER agent

# Expose common ports (can be overridden by specific agents)
# 8000-8010: API services
# 9000-9010: Dashboard/UI services
# 6006: TensorBoard
EXPOSE 8000-8010 9000-9010 6006

# Default command (override in specific agents)
CMD ["/bin/bash"]

# Health check (override in specific agents)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"
