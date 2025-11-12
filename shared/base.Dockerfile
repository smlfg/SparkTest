# Shared Base Docker Image for All Agents
# Provides NVIDIA GPU support with PyTorch and CUDA toolkit

FROM nvcr.io/nvidia/pytorch:24.10-py3

# Metadata
LABEL maintainer="DGX Spark Team"
LABEL description="Base image for all DGX Spark Playbook agents"
LABEL version="1.0.0"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # NVIDIA and CUDA
    nvidia-container-toolkit \
    cuda-toolkit-12-3 \
    # Build essentials
    build-essential \
    cmake \
    git \
    wget \
    curl \
    # Python development
    python3-dev \
    python3-pip \
    # Networking
    net-tools \
    iputils-ping \
    dnsutils \
    # Utilities
    vim \
    tmux \
    htop \
    nvtop \
    # Libraries
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    # Graphics (for visualization)
    graphviz \
    graphviz-dev \
    # Video processing
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install common Python dependencies used across all agents
RUN pip install --no-cache-dir \
    # Async and HTTP
    aiohttp>=3.9.0 \
    httpx>=0.26.0 \
    # Web frameworks
    fastapi>=0.109.0 \
    uvicorn[standard]>=0.27.0 \
    # Data processing
    numpy>=1.26.0 \
    pandas>=2.2.0 \
    # Configuration
    pyyaml>=6.0.0 \
    python-dotenv>=1.0.0 \
    # Logging
    python-json-logger>=2.0.0 \
    # Monitoring
    prometheus-client>=0.19.0 \
    # Testing
    pytest>=7.4.0 \
    pytest-asyncio>=0.23.0 \
    # Type hints
    typing-extensions>=4.9.0

# Create application directory
RUN mkdir -p /app/shared /app/logs /app/data

# Set working directory
WORKDIR /app

# Copy shared utilities
COPY shared/ /app/shared/

# Add shared Python modules to PYTHONPATH
ENV PYTHONPATH=/app:${PYTHONPATH}

# Health check (override in agent-specific Dockerfiles)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/shared/health_check.py || exit 1

# Default command (override in agent-specific Dockerfiles)
CMD ["python", "--version"]
