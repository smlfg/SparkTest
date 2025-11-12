# Agent 2: Dashboard And Visualization Agent

FROM nvcr.io/nvidia/pytorch:24.10-py3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nvidia-container-toolkit \
    cuda-toolkit-12-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy shared utilities first (for caching)
COPY shared/ /app/shared/

# Install Python dependencies
RUN pip install --no-cache-dir \
    pyyaml \
    requests \
    fastapi \
    uvicorn \
    prometheus-client \
    python-json-logger

# Copy agent-specific files
COPY agents/agent2_dashboard/ /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV CONFIG_PATH=/app/config.yaml
ENV AGENT_NAME=agent2_dashboard

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from shared.health_check import check_service; import sys; sys.exit(0 if check_service(8002, '/health') else 1)"

# Expose port
EXPOSE 8002

# Run the agent
CMD ["python", "main.py"]
