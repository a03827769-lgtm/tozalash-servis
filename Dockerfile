# =====================================================
# Multi-Stage Production Dockerfile for Tozalash Servis
# Stage 1: Builder (Compilation & Dependency Wheel Installation)
# Stage 2: Lean Runtime (Optimized for Free Cloud Tiers - Koyeb / Render)
# =====================================================

# --- Stage 1: Builder ---
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# System dependencies for compiling binary wheels and audio extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and core build tools via standard PyPI
RUN pip install --upgrade pip setuptools wheel

# Copy requirements definitions first for Docker layer caching
COPY requirements.txt requirements_phase2.txt ./

# Install packages into the isolated virtual environment
RUN pip install --no-cache-dir \
    --default-timeout=600 \
    -r requirements.txt \
    -r requirements_phase2.txt

# --- Stage 2: Lean Runtime ---
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Minimal runtime dependencies (libpq5, ffmpeg, libsndfile1, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Copy application source code
COPY . .

# Security hardening: Create non-root user (UID 10001) and configure directories
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser && \
    mkdir -p /app/data /app/logs /app/data/audio_cache /app/data/downloads && \
    chown -R appuser:appgroup /app /opt/venv

USER appuser

EXPOSE 8000

# Dynamic port health check with graceful start period
HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch unified async supervisor
CMD ["python", "main.py"]
