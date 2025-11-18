# Multi-stage Dockerfile for AI File Classifier
# Optimized for production deployment with minimal image size

# ============================================================================
# Builder Stage: Install dependencies
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency definition (not source code - for better caching)
COPY pyproject.toml ./

# Install Python dependencies to isolated location
# This avoids package vs script confusion and properly installs dependencies
RUN pip install --target=/app/deps --no-cache-dir .

# ============================================================================
# Runtime Stage: Minimal production image
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies and create non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser appuser \
    && mkdir -p /app/input /app/output \
    && chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /app/deps /usr/local/lib/python3.11/site-packages/

# Switch to non-root user for security
USER appuser

# Copy application code (as appuser, last for optimal layer caching)
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser prompts/ ./prompts/

# Set Python to run in unbuffered mode (better for Docker logs)
ENV PYTHONUNBUFFERED=1

# Set entrypoint to the application
ENTRYPOINT ["python", "main.py"]

# Default command (can be overridden)
CMD ["--help"]
