# Shared Base Image for DGX Spark Playbooks
# Based on NVIDIA PyTorch with CUDA support

FROM nvcr.io/nvidia/pytorch:24.10-py3

LABEL maintainer="DGX Spark Team"
LABEL description="Base image for all DGX Spark agents with NVIDIA GPU support"
LABEL version="1.0.0"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Update and install essential packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # System tools
    curl \
    wget \
    vim \
    git \
    htop \
    tmux \
    jq \
    # Build tools
    build-essential \
    cmake \
    pkg-config \
    # NVIDIA tools
    nvidia-container-toolkit \
    cuda-toolkit-12-3 \
    # Network tools
    net-tools \
    iputils-ping \
    netcat \
    # Monitoring tools
    sysstat \
    iotop \
    # Python dependencies
    python3-dev \
    python3-pip \
    python3-setuptools \
    # Ansible support
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    # API frameworks
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    aiohttp==3.9.1 \
    # Data handling
    pydantic==2.5.3 \
    pyyaml==6.0.1 \
    # HTTP clients
    requests==2.31.0 \
    httpx==0.26.0 \
    # Configuration
    python-dotenv==1.0.0 \
    # Logging
    python-json-logger==2.0.7 \
    loguru==0.7.2 \
    # Monitoring
    prometheus-client==0.19.0 \
    psutil==5.9.7 \
    # Testing
    pytest==7.4.4 \
    pytest-asyncio==0.23.3 \
    pytest-cov==4.1.0 \
    # GPU monitoring
    py3nvml==0.2.7 \
    gpustat==1.1.1

# Install NVIDIA libraries
RUN pip install --no-cache-dir \
    nvidia-ml-py3 \
    pynvml

# Create application directory structure
RUN mkdir -p /app /app/data /app/logs /app/config /app/shared

# Add health check script
COPY shared/health_check.py /app/shared/
COPY shared/utils/ /app/shared/utils/

# Set working directory
WORKDIR /app

# Add non-root user for security
RUN useradd -m -u 1000 -s /bin/bash sparkuser && \
    chown -R sparkuser:sparkuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 /app/shared/health_check.py --self-check || exit 1

# Default command
CMD ["/bin/bash"]
