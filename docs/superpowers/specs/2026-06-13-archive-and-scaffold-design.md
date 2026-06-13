# Design: Archive Prototype & Scaffold New Module Structure

**Date:** 2026-06-13
**Status:** Approved
**Scope:** Repo preparation step before Phase 0 implementation begins.

## Problem

The repository contains a working prototype (ChromaDB + flat files + vanilla JS) whose structure is incompatible with the target architecture. The prototype is "prior art only" — its logic informs future phases but the target is a clean-slate rebuild.

## Decision

Option B — filesystem move + single commit. `git mv` precision is overkill for files treated as read-only reference; the repo-level history is fully preserved regardless.

## What Gets Archived (`_archive/`)

| Source | Destination |
|---|---|
| `backend/` | `_archive/backend/` |
| `scrapers/` | `_archive/scrapers/` |
| `frontend/` | `_archive/frontend/` |
| `notebooks/` | `_archive/notebooks/` |
| `requirements.txt` | `_archive/requirements.txt` |
| `data/` (gitignored) | `_archive/data/` (OS-level only) |

`.gitignore` updated: `data/` → `_archive/data/`.

## What Stays in Root

`CLAUDE.md`, `README.md`, `.env.example`, `.env` (gitignored), `.gitignore`, `docs/`.

## New Skeleton

```
ingestion/__init__.py
nlp/__init__.py
enrich/__init__.py
api/__init__.py
web/.gitkeep
```

Each `__init__.py` contains a single docstring matching the CLAUDE.md phase description. No implementation.

## Why This Structure

Matches the target module boundaries from `docs/system-design.md` exactly. The archive stays visible in the working tree so it can be audited phase-by-phase as each build phase starts.

## Commit

`chore: archive prototype, scaffold new module structure`
