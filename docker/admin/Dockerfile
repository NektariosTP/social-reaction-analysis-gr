# --- builder: install base deps into /app/.venv ---
FROM python:3.11-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

ENV UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# --- runtime: clean image with just the venv + source (no toolchain, no uv) ---
FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY admin/ ./admin/
# enrich.axes only — pure-Python label constants, no heavy deps pulled.
COPY enrich/ ./enrich/

EXPOSE 8001
CMD ["uvicorn", "admin.main:app", "--host", "0.0.0.0", "--port", "8001"]
