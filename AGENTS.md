# Repository Guidelines

## Project Structure & Module Organization
- Root is a Frappe bench; run commands from the repo root.
- `apps/ferum_custom` holds custom business logic, DocTypes under `doctype/**`, API in `api/`, and assets in `public/`.
- `apps/frappe` is the framework and `apps/erpnext` the base ERP modules—avoid touching unless coordinated.
- `sites/` stores site configs and built assets; `sites/test_site` is the local/test target.
- `config/` contains bench infra configs (nginx, redis); `scripts/` houses helper and pre-commit utilities; `docs/` keeps architecture/runbooks; `tests/` contains bench-level test scaffolding.

## Build, Test, and Development Commands
- `bench start` – run dev services (web, scheduler, websocket, assets).
- `bench watch` – live-rebuild JS/CSS while editing assets.
- `bench build` – one-off production asset build before packaging images.
- `bench --site test_site migrate` – apply migrations/patches to the local test site.
- `./env/bin/pytest apps/ferum_custom/ferum_custom/tests` – full custom app suite; target a file for focused runs.
- `bench --site test_site run-tests --app ferum_custom` – framework runner when you need DB isolation per test (see `make bench-test`).
- `make lint | make format | make test [FILE=...] | make bench-test | make ci | make ci-bench | make build-prod | make verify | make docker-build | make docker-push | make deploy | make bootstrap-site` – shortcuts for the above (see `Makefile`); `make clean` drops caches/coverage safely. `DOCKER_TAG`/`DOCKER_REGISTRY`/`DOCKER_PLATFORM`/`BENCH_SITE` vars are overridable.

## Coding Style & Naming Conventions
- Python in `apps/ferum_custom` uses Black (line length 100), isort, Ruff (E/F/W/I/B), and mypy (py3.12). Run `pre-commit run --all-files` before committing.
- JS/TS/markup in `apps/ferum_custom` is formatted with Prettier and linted via ESLint 9.
- Use snake_case modules and keep DocType package names aligned (`doctype/order/order.json` + `order.py` with `__init__.py` in the package).

## Testing Guidelines
- Smoke paths are listed in `docs/runbooks/testing.md`: service requests, finance, portal JWT, integrations health, migrations/ETL.
- Preferred commands: `./env/bin/pytest apps/ferum_custom/ferum_custom/tests/test_service_requests.py` (service flow), `.../test_finance_flows.py`, `.../test_portal_api.py`, `.../test_integrations_telegram.py`, `.../test_integrations_drive.py`.
- Use `sites/test_site` and avoid mutating shared fixtures; add new fixtures at the app level, not bench root.

## Commit & Pull Request Guidelines
- History follows Conventional Commit variants (`chore(codex):…`, `docs(release):…`, `deploy:`); keep the type prefix and concise scope.
- PRs should note the site used, migrations executed, test commands + outcomes, and risk/rollback notes; include screenshots for UI changes.
- Keep changes focused on `apps/ferum_custom` unless coordinating framework edits; link issues/tasks when available.

## Quick Links
- Runbook: `docs/runbooks/testing.md` for smoke flows and commands.
- Security: `docs/runbooks/secret_management.md` and `docs/runbooks/secret_rotation_log.md`.
- Infra: `docs/runbooks/monitoring.md`, `docs/architecture/architecture_overview.md`, `docs/finish/finish_plan.md`.

## Troubleshooting
- `bench --site test_site clear-cache && bench --site test_site restart` to resolve stale cache/websocket issues.
- If migrations fail, run `bench --site test_site migrate --skip-failing` only after logging the failing patch and coordinating a fix.
- Asset glitches: `bench watch` for dev; `bench build --force` before retrying production packaging.

## Security & Configuration Tips
- Never commit secrets; use `.env.example` as the template and render via `scripts/render_env.py` or `scripts/render_env_from_secrets.sh`.
- Infra configs in `config/` (redis, nginx) should be changed with ops awareness; avoid ad-hoc port/host edits.
- Prefer ORM/API calls over raw SQL; the forbidden-patterns pre-commit hook blocks unsafe queries or stray prints.
