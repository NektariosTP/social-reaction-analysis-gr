"""Dump the FastAPI OpenAPI schema to web/openapi.json (offline, no DB needed).

Run: uv run python -m scripts.export_openapi
Then: cd web && npm run generate-client
"""
from __future__ import annotations

import json
from pathlib import Path

from api.main import app

_OUT = Path(__file__).resolve().parent.parent / "web" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    _OUT.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {_OUT}")


if __name__ == "__main__":
    main()
