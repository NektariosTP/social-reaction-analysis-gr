FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen
RUN uv run python -m spacy download el_core_news_md

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY ingestion/ ./ingestion/
COPY nlp/ ./nlp/
COPY enrich/ ./enrich/
COPY reactions/ ./reactions/
COPY worker/ ./worker/

CMD ["uv", "run", "python", "-m", "worker.run"]
