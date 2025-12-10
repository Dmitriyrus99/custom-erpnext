### Ferum Custom

Ferum Custom is an ERPNext-based system designed to manage and streamline operations for Ferum. It includes custom modules for issue management, invoicing, and integrations with external services like Google Drive, Google Sheets, and Telegram.

### Telegram Bot Integration

This repository includes a Telegram bot that integrates with the Ferum Custom ERP system. The bot allows users to perform the following actions:

-   **Create Issues**: Quickly create new issues directly from Telegram.
-   **List Issues**: View a list of your own or assigned issues.
-   **Update Issue Status**: Change the status of an issue using inline buttons.
-   **Attach Files**: Attach photos and documents to issues and timesheets.

For detailed setup and deployment instructions, see the `telegram_bot/README.md` file.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app ferum_custom
```

> **Note**
>
> The project depends on the Frappe framework. Its version is pinned but commented out in `pyproject.toml` because Frappe is installed and managed through the `bench` CLI.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/ferum_custom
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.

### Setup & Operations

- See `install.md` for detailed role mapping, Customer‑based Client access (User Permission), and integration settings for Google Drive/Sheets and Telegram.

### License

mit
