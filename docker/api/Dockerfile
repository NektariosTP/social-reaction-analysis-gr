FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY api/ ./api/
COPY ingestion/ ./ingestion/
COPY nlp/ ./nlp/
COPY enrich/ ./enrich/
COPY stats/ ./stats/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
