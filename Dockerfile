# ==============================================================================
# Orion B2B Lead Intelligence & Multi-Agent QA Engine
# Enterprise Multi-Stage Dockerfile (Python 3.11 Slim)
# Optimized for Linux server production deployments & container orchestration
# ==============================================================================

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8550

WORKDIR /app

# Install minimal OS dependencies for health checks & network verification
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY core/ ./core/
COPY ui/ ./ui/
COPY data/.gitkeep ./data/.gitkeep
COPY main.py .
COPY seed_demo_data.py .
COPY export_web_demo.py .

# Create non-privileged user for security compliance (RODO/GDPR & CIS Docker Benchmark)
RUN useradd -m -u 10001 orionuser && \
    mkdir -p /app/data && \
    chown -R orionuser:orionuser /app

USER orionuser

# Seed initial schema if needed
RUN python seed_demo_data.py --reset

EXPOSE 8550

# Automated Docker Container Healthcheck using Orion Health Monitor
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python core/health_monitor.py --db data/leads.db --max-latency 50.0 || exit 1

# Default runtime entrypoint: Launch Flet Web Dashboard
CMD ["python", "main.py", "--web"]
