# JAX ARM64 Optimized Container
# Optimized for Apple Silicon (M1/M2/M3) and ARM64 architectures

FROM arm64v8/ubuntu:22.04

LABEL maintainer="Agent3 Dev Environments"
LABEL description="JAX optimized for ARM64 with GPU support"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.11 \
    JAX_PLATFORM_NAME=cpu \
    XLA_FLAGS="--xla_force_host_platform_device_count=8" \
    JAX_ENABLE_X64=True

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    wget \
    ca-certificates \
    libblas-dev \
    liblapack-dev \
    libhdf5-dev \
    libopenblas-dev \
    gfortran \
    pkg-config \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set python3 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1

# Upgrade pip and install build tools
RUN python3 -m pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    wheel

# Install JAX with optimizations for ARM64
# Using CPU-only version by default, can be customized for GPU
RUN python3 -m pip install --no-cache-dir \
    "jax[cpu]>=0.4.20" \
    jaxlib \
    numpy \
    scipy \
    && python3 -m pip cache purge

# Install additional ML/Scientific computing packages
RUN python3 -m pip install --no-cache-dir \
    optax \
    flax \
    chex \
    dm-haiku \
    equinox \
    diffrax \
    orbax-checkpoint \
    matplotlib \
    pandas \
    scikit-learn \
    jupyter \
    jupyterlab \
    ipykernel \
    && python3 -m pip cache purge

# Install performance profiling tools
RUN python3 -m pip install --no-cache-dir \
    jax-profiler \
    tensorboard \
    && python3 -m pip cache purge

# Create workspace directory
RUN mkdir -p /workspace
WORKDIR /workspace

# Create a non-root user
RUN useradd -m -s /bin/bash jaxuser && \
    chown -R jaxuser:jaxuser /workspace

# Copy entrypoint script
COPY jax-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/jax-entrypoint.sh

USER jaxuser

# Expose Jupyter port
EXPOSE 8888

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/jax-entrypoint.sh"]
CMD ["bash"]
