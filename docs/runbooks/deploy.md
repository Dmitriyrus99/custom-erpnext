# Deploy runbook

This runbook describes how to deploy the Frappe stack with the new CI/CD workflow and the helper script in `scripts/deploy.sh`.

## CI/CD contract

- `[lint]`, `[test]`, and `[build]` jobs are always executed on `push`, `pull_request`, and manual workflows.
- The `[deploy]` job runs only when the workflow is triggered manually (`workflow_dispatch`) and requires:
  - `GHCR_TOKEN` secret with permission to push to `ghcr.io`.
  - `DEPLOY_KEY`, `DEPLOY_USER`, `DEPLOY_HOST`, and `DEPLOY_PATH` for SSH control of the production host.
  - Optional `DEPLOY_BRANCH` (default `main`) and `DEPLOY_BACKUP_FILE` (default `backups/latest.dump`).

During the `[deploy]` job the workflow:

1. Logs into GitHub Container Registry and builds/pushes the Docker image defined in `apps/ferum_custom/Dockerfile`.
2. Connects to the production host, pulls the latest branch, and invokes `./scripts/deploy.sh deploy <image>` with the pushed image.

## Editable Frappe in CI/CD

Immediately after cloning `custom-erpnext` and before running any `bench` commands, ensure Frappe is installed in editable mode within `frappe-bench/apps/frappe`. Add the following snippet to your CI/CD workflow or bootstrapping script:

```bash
# Ensure frappe sits under apps/ and is installed editable
cd frappe-bench
[ -d "frappe" ] && [ ! -d "apps/frappe" ] && mkdir -p apps && mv frappe apps/
./env/bin/pip install -e apps/frappe
```

On CI runners keep this before any `bench` invocation so changes under `apps/frappe` obey development flow. If the repo was cloned directly under `frappe-bench/apps`, the script simply installs the existing path (`pip install -e apps/frappe`).

## Preparing for deploy

1. Keep recent backups in `backups/` (e.g. `backup-YYYYMMDD.dump` or `backups/latest.dump`). The deploy script expects a PostgreSQL dump or plain SQL file for rollbacks (`pg_restore` is used unless the file ends in `.sql`).
2. Ensure `.env` is populated on the server with production secrets (the compose file uses `env_file: .env`). Never copy local secrets via CI.
3. Set the required GitHub secrets in Settings > Secrets to allow the workflow to log into GHCR and SSH to the host.

## Using `scripts/deploy.sh`

The script accepts two commands:

```bash
./scripts/deploy.sh deploy <image>
./scripts/deploy.sh rollback [image] [backup-file]
```

- `deploy` pulls `backend`, `worker`, and `scheduler` images by assigning `ERPNEXT_IMAGE=<image>` before each `docker compose` invocation and restarts those services.
- `rollback` brings the stack back to the previous image stored in `.deploy_state` (you can override it with the first argument) and restores PostgreSQL from the provided backup file or `backups/latest.dump`.
- The script writes the last `CURRENT_IMAGE`, `PREVIOUS_IMAGE`, and `ROLLBACK_BACKUP` values into `.deploy_state` so the rollback knows what to revert to.

Before running deploys, ensure the production host has network access to the registry and that `docker compose` is installed there.

## Manual deploy example

1. Build the image locally (optional) and push it to the registry you control.
2. On the production host, run:

   ```bash
   ./scripts/deploy.sh deploy ghcr.io/your-org/erpnext:<tag>
   ```

3. After verifying the application is healthy, ensure a new backup is saved under `backups/latest.dump` for the next rollback.

## Rollback steps

1. Copy the desired backup to the production host if it is not already there, e.g. `scp backup-2023-10-01.dump $DEPLOY_USER@$DEPLOY_HOST:/opt/erpnext/backups/latest.dump`.
2. On the production host run:

   ```bash
   ./scripts/deploy.sh rollback
   ```

   or supply explicit values:

   ```bash
   ./scripts/deploy.sh rollback ghcr.io/your-org/erpnext:previous-tag backups/backup-2023-10-01.dump
   ```

3. Confirm the application is responsive and that the database was restored successfully.
