# Repository Guidelines

## Project Structure & Module Organization
- `backend/` hosts the FastAPI service (`main.py`) and dependency pinning in `requirements.txt`; database DDL lives in `schema.sql`.
- `frontend/` contains the static dashboard HTML; update shared styles or scripts in place to keep CDN links and IDs stable.
- `scripts/` bundles operational helpers (`create_admin.py`, `import_agents.py`, migrations) that should be executed from inside the API container.
- `docs/` stores deployment procedures, while `data/` is the bind-mounted SQLite volume—avoid committing generated `leads.db`.

## Build, Test, and Development Commands
- `docker-compose up -d` boots the API (`newhomes-api`) and the Nginx proxy; add `--build` after dependency or Dockerfile edits.
- `docker-compose logs -f api` tails backend output for request tracing and background jobs.
- `docker exec -it newhomes-api python scripts/create_admin.py` seeds the first administrator after a clean deploy.
- For local-only tweaks, `pip install -r backend/requirements.txt && uvicorn backend.main:app --reload` mirrors the container process with live reload.

## Coding Style & Naming Conventions
- Backend Python sticks to 4-space indentation, type-hinted FastAPI endpoints, and Pydantic models with descriptive class names (`VisitorCreate`, `AgentUpdate`).
- Prefer helper functions over inline SQL; keep database work inside the provided `get_db()` context manager for connection hygiene.
- Frontend files are vanilla HTML/ES6; use kebab-case CSS classes and cluster related DOM helpers near their modal or form markup.

## Testing Guidelines
- Automated tests are not yet committed; when adding coverage, place `test_*.py` under `backend/tests/` and run `pytest backend/tests`.
- Use SQLite fixtures that mirror `schema.sql`, and hit endpoints through FastAPI's `TestClient` rather than manipulating tables directly.
- Document manual QA steps (visitor creation, CINC sync, exports) in the PR whenever automation is unavailable.

## Commit & Pull Request Guidelines
- Git history favors short, imperative summaries (`add visitor bug fix`, `update deployment docs`); keep messages under 60 characters and expand detail in the body when needed.
- Scope each PR to a single concern, link the tracking issue, and note any schema changes or new environment variables up front.
- Attach before/after screenshots for UI tweaks and paste the exact command output for scripts or migrations you executed.

## Security & Configuration Tips
- Never commit `.env` or `credentials.json`; exchange updates through the secure channel referenced in `DEPLOYMENT.md`.
- Rotate the default super-admin credentials immediately and record secret hand-offs in deployment notes for continuity.
