# shared/base.Dockerfile
# Base Docker image for all DGX Spark agents
# Includes NVIDIA PyTorch and CUDA toolkit for GPU acceleration

FROM nvcr.io/nvidia/pytorch:24.10-py3

# Install NVIDIA container toolkit and CUDA toolkit
RUN apt-get update && apt-get install -y \
    nvidia-container-toolkit \
    cuda-toolkit-12-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy shared utilities
COPY shared/ /app/shared/

# Install Python dependencies (common across all agents)
RUN pip install --no-cache-dir \
    pyyaml \
    requests \
    fastapi \
    uvicorn \
    prometheus-client \
    python-json-logger

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from shared.health_check import check_service; import sys; sys.exit(0 if check_service(8000, '/health') else 1)"

# Default command (to be overridden by specific agents)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
