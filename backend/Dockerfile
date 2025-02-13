# Build stage
FROM python:3.11-slim-bookworm AS builder

# Install uv and git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install dependencies first (for better caching)
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy and install the project
COPY backend/ .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode --no-editable

# Final stage
FROM python:3.11-slim-bookworm

# Create non-root user
RUN useradd -m -U app

# Copy only the venv from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
USER app
WORKDIR /app
