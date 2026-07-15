FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY admin/ ./admin/
COPY enrich/ ./enrich/

EXPOSE 8001
CMD ["uv", "run", "uvicorn", "admin.main:app", "--host", "0.0.0.0", "--port", "8001"]
