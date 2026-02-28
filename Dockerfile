# syntax=docker/dockerfile:1

############################
# 1) Builder (deps)
############################
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps
# - ca-certificates: TLS para Mongo Atlas
# - build-essential/gcc/pkg-config: para compilar wheels si aplica
# - portaudio19-dev: SOLO si realmente lo ocupas (si no, bórralo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    gcc \
    pkg-config \
    portaudio19-dev \
  && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy lock files first (mejor cache)
COPY pyproject.toml uv.lock ./

# Install deps into /app/.venv
RUN uv sync --frozen --python 3.13 --no-dev


############################
# 2) Runtime
############################
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Runtime deps
# - ca-certificates: TLS Mongo Atlas
# - libportaudio2: SOLO si lo ocupas (si no, bórralo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libportaudio2 \
  && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy only your source code
# ✅ OJO: ya NO copiamos "schemas/" en raíz
COPY app/ /app/app
COPY agents/ /app/agents
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

# Use venv by default
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Optional: healthcheck (requiere /health)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]