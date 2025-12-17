# Testing & QA Runbook

## Smoke scenarios

1. **Service Request flow**
   - Create a Service Request via API/portal.
   - Update status to `In Progress` → `Completed`.
   - Check that notifications & contracts update in `Service Request` doc.  
     _Command_: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_service_requests.py`

2. **Finance flow**
   - Create an Invoice → submit → create Payment entry.
   - Ensure Status transitions and payments link.  
     _Command_: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_finance_flows.py`

3. **Portal token / JWT**
   - Request `portal_token`, call `create_service_request` with JWT header.  
     _Command_: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_portal_api.py`

4. **Integrations health**
   - Telegram health check (`ferum_custom.api.telegram_bot.health`).
   - Drive health check (`/api/method/ferum_custom.api.drive.health` wraps the internal `drive.healthcheck`).  
     _Command_: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_integrations_telegram.py` + `test_integrations_drive.py`

5. **Portal health + rate limiting**
   - Ensure `portal_token()` rejects Guests without JWT and rate limits (`_check_new_request_rate_limit`).  
     _Command_: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_portal_api.py`

## Integration & security coverage

- JWT enforcement guard: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_api_auth.py`
- Google Sheets sync resilience: `./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/test_integrations_sheets.py`

## Migration & domain/ETL tests

- Use `apps/apps/ferum_custom/ferum_custom/tests/test_migrations.py` to verify contract normalization + Data Issue logging.
- Run `apps/apps/ferum_custom/ferum_custom/tests/domain/test_service_application.py` to cover the high-level service request helpers (creation, listing filters).
- Run `apps/apps/ferum_custom/ferum_custom/tests/test_etl.py` to ensure `Stg Raw` ingestion honors company metadata and renders JSON payloads correctly.

## Running all tests

```bash
./env/bin/pytest apps/apps/ferum_custom/ferum_custom/tests/
```

Include these commands in CI Stage 6.
