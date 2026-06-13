FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY api/ ./api/
COPY ingestion/ ./ingestion/
COPY nlp/ ./nlp/
COPY enrich/ ./enrich/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
