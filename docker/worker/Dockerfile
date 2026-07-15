FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen
RUN uv run python -m spacy download el_core_news_md

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY ingestion/ ./ingestion/
COPY nlp/ ./nlp/
COPY enrich/ ./enrich/
COPY worker/ ./worker/

CMD ["uv", "run", "python", "-m", "worker.run"]
