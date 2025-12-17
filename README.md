# Frappe/ERPNext v15 - Ferum Customizations

This project is a Frappe/ERPNext v15 system, with custom modifications and integrations tailored for Ferum's operations.

## Project Goals

- **Migration:** Transitioned from custom DocTypes (e.g., Service Request, Service Project) to standard ERPNext DocTypes (Issue, Project, Asset, Timesheet, Sales Invoice).
- **Integrations:** Key integrations include a Telegram Bot (Aiogram), Google Drive (File Sync), and Google Sheets (Reporting).
- **Operational Efficiency:** Streamlined workflows for service requests, project management, and financial reporting.

## Telegram Bot Integration

- **Create Issues**: Quickly create new issues directly from Telegram.
- **List Issues**: View a list of your own or assigned issues.
- **Update Issue Status**: Change the status of an issue using inline buttons.
- **Attach Files**: Attach photos and documents to issues and timesheets.

## Technology Stack

- **Backend:** Frappe Framework v15, ERPNext, Python 3.12, FastAPI (for custom APIs).
- **Database:** PostgreSQL 13.
- **Caching/Queue:** Redis.
- **Containerization:** Docker.
- **CI/CD:** GitHub Actions.
- **Bot Framework:** Aiogram.
- **External APIs:** Google Drive API, Google Sheets API.

## Setup & Installation

Refer to the project's `docs/` directory for detailed setup instructions, including environment configuration, dependency installation, and bench setup.

## Running the Application

1. **Bench Setup:** Ensure you have a Frappe bench environment set up.
2. **Start Services:** Use `bench start` to run the Frappe development server.

## Testing

Unit and integration tests are located in `apps/ferum_custom/ferum_custom/tests/` and `apps/ferum_custom/telegram_bot/telegram_bot/tests/`.

Run tests using:
```bash
./env/bin/pytest apps/ferum_custom/ferum_custom/tests
./env/bin/pytest apps/ferum_custom/telegram_bot/telegram_bot/tests
```

Coverage reports can be generated via `pytest --cov=ferum_custom --cov-report=xml`.

## CI/CD Pipeline

The CI/CD pipeline (defined in `.github/workflows/ci.yml`) includes:

- **Linting & Secrets Scanning:** `pre-commit` checks and `gitleaks`.
- **Testing:** `pytest` with `pytest-cov` runs unit and e2e tests, generating XML coverage reports.
- **Migrations:** `bench migrate` is run to apply database schema changes.
- **Build:** `bench build` compiles static assets (JS/CSS) for the custom app.
- **Deployment:** Docker image build/push for main branch, manual trigger deployment to staging/prod via SSH.

## Documentation

Comprehensive documentation is available in the `docs/` directory, covering:

- **Architecture Overview:** `docs/architecture/architecture_overview.md`
- **Delivery Plan:** `docs/delivery_plan.md`
- **Infrastructure & CI/CD:** `docs/infrastructure_and_ci.md`
- **Roles & ACL:** `docs/roles_and_acl.md`
- **Integrations:** `docs/integrations/` (e.g., `google_drive_setup.md`, `google_sheets_setup.md`)
- **Runbooks:** `docs/runbooks/` for operational guidance.
