FROM python:3.11-slim-bookworm

# Install uv and git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN useradd -m -U app

# Set working directory
WORKDIR /app

# Install big dependencies first (for better caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && uv pip install vllm>=0.7.2 torch>=2.5.1

# Install the rest of the dependencies
COPY --chown=app:app backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode --no-install-project

# Copy and install the project
COPY --chown=app:app backend/rrc/ ./rrc/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode --reinstall-package rrc --no-editable

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV RRC_DATA_ROOT=/data/output
ENV RRC_IMAGE_ROOT=/data/images
USER app

LABEL org.opencontainers.image.source=https://github.com/reglab/rrc-pipeline
