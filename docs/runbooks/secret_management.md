# Secret Management Runbook

This runbook ensures that every sensitive value (JWT secret, DB password, integrations, dashboards) lives outside the repo and is materialized at runtime through the rendering scripts under `scripts/`.

## 1. Secret inventory

| NAME | Description | Consumers | Owner |
| --- | --- | --- | --- |
| `FERUM_JWT_SECRET` | JWT/signing key for portal/API tokens | Portal endpoints, integrations, tests | Security Engineer |
| `FERUM_TELEGRAM_BOT_TOKEN`, `FERUM_TELEGRAM_WEBHOOK_SECRET` | Telegram bot credentials and webhook guard | Integrations Engine, CI smoke flows | Integrations Engineer |
| `FERUM_GOOGLE_SERVICE_ACCOUNT_JSON` | Drive/Sheets service account payload | Google Drive sync, invoice exports | Integrations Engineer |
| `FERUM_GOOGLE_DRIVE_ROOT_FOLDER_ID`, `FERUM_GOOGLE_SHEET_NAME` | Drive folder/sheet targets | Drive exports, invoice sync | Integrations Engineer |
| `POSTGRES_HOST/PORT/DB/USER/PASSWORD` | Primary PostgreSQL access | Backend, worker, scheduler, CI | DevOps |
| `REDIS_CACHE`, `REDIS_QUEUE`, `REDIS_SOCKETIO` | Redis endpoints for cache, queue and socketio | Backend + queue workers | DevOps |
| `SENTRY_DSN`, `FERUM_SENTRY_DSN`, `FRAPPE_SENTRY_DSN` | Sentry DSNs for the ERPNext/Frappe stack | Backend, workers, portal | Observability / Security |
| `TRAEFIK_DASHBOARD_HOST`, `TRAEFIK_DASHBOARD_BASIC_AUTH` | Traefik dashboard authentication | Monitoring / DevOps | DevOps |
| `GRAFANA_USER`, `GRAFANA_PASSWORD` | Grafana credentials | Monitoring dashboards | DevOps |
| `FERUM_SECRET_ROTATION_SCHEDULE` | Last rotation cadence/note | Runbooks & auditors | Security Engineer |

## 2. Mapping to Secret Manager

### Vault (HashiCorp KV v2)

1. Enable KV v2 if not already:  
   `vault secrets enable -path=secret kv-v2`
2. Write all keys under a single path per env, e.g.:
   ```bash
   vault kv put secret/ferum/dev \
     FERUM_JWT_SECRET=<secret> \
     FERUM_TELEGRAM_BOT_TOKEN=<token> \
     FERUM_TELEGRAM_WEBHOOK_SECRET=<secret> \
     FERUM_GOOGLE_SERVICE_ACCOUNT_JSON='<json payload>' \
     FERUM_GOOGLE_DRIVE_ROOT_FOLDER_ID=<drive-id> \
     FERUM_GOOGLE_SHEET_NAME=<sheet> \
     POSTGRES_HOST=postgres \
     POSTGRES_PORT=5432 \
     POSTGRES_DB=erpnext \
     POSTGRES_USER=frappe \
     POSTGRES_PASSWORD=<secret> \
     REDIS_CACHE=redis://redis-cache:6379 \
     REDIS_QUEUE=redis://redis-queue:6379 \
     REDIS_SOCKETIO=redis://redis-socketio:6379 \
     SENTRY_DSN=<dsn> \
     FERUM_SENTRY_DSN=<dsn> \
     FRAPPE_SENTRY_DSN=<dsn> \
     TRAEFIK_DASHBOARD_HOST=traefik.example.com \
     TRAEFIK_DASHBOARD_BASIC_AUTH=traefik:<htpasswd> \
     GRAFANA_USER=admin \
     GRAFANA_PASSWORD=<secret> \
     FERUM_SECRET_ROTATION_SCHEDULE=weekly
   ```
3. Use policies so CI runners and deploy scripts have `read` access only to the required path. Never hardcode tokens in the repo.

### AWS SSM (Parameter Store)

1. Store each key as `/ferum/<env>/<KEY>` with type `SecureString`.  
2. Example command:
   `aws ssm put-parameter --name /ferum/dev/FERUM_JWT_SECRET --value "<secret>" --type SecureString --overwrite`
3. Grant IAM roles limited to `ssm:GetParametersByPath` for `/ferum/dev`.

## 3. Rendering `.env`

1. Generate the secrets blob with `scripts/render_env_from_secrets.sh`.
   ```bash
   VAULT_ADDR=https://vault.example.com VAULT_TOKEN=${VAULT_TOKEN} \
     ./scripts/render_env_from_secrets.sh --provider vault --path secret/ferum/dev --output .env.secrets
   ```
   Or (AWS SSM):
   ```bash
   AWS_PROFILE=ferum-dev \
     ./scripts/render_env_from_secrets.sh --provider aws-ssm --path /ferum/dev --output .env.secrets
   ```
2. Merge with the template:
   ```bash
   ./scripts/render_env.py --input .env.example --output .env --extra-file .env.secrets
   ```
   Extra files (`--extra-file`) can be repeated (e.g. for Vault + additional overrides).
3. Always verify sensitive values remain external:
   `grep -E '^FERUM_JWT_SECRET|REDIS_' .env`

## 4. Scripts overview

- `scripts/render_env_from_secrets.sh`: fetches secrets from Vault or AWS SSM and writes `KEY=VALUE` lines (supports `--provider vault|aws-ssm`, `--path`, `--output`, `--format=json`).
- `scripts/render_env.py`: merges `.env.example` with the rendered files, preserves comments/structure, and emits the consolidated `.env` that Docker Compose and CI will read.

Both scripts add generated files to `.gitignore` by default; never commit `.env` or `.env.secrets`.

## 5. CI/CD / Docker integration

- In GitHub Actions, add a `render-env` step before lint/test/build/deploy. Machines must have vault/SSM access and CLI tools installed.
- Keep `.env` out of Git. The compose file and `scripts/deploy.sh` rely on `env_file: .env`.
- Backups and migrations should source `.env` via `set -a && source .env && set +a` before running bench commands.

## 6. Rotation & logging

- Log every rotation inside `docs/runbooks/secret_rotation_log.md` (trigger, approvers, affected envs).
- Update `FERUM_SECRET_ROTATION_SCHEDULE` after each rotation.
- For emergency rotation: update the secret, rerender `.env`, restart the services (backend, worker, scheduler).
