# Deployment and CI/CD

This guide describes how to deploy Ferum Customizations with Docker Compose and how the project is validated in continuous integration.

## Deployment

1. **Prepare configuration**
   - Create a `.env` file as shown in [DEPLOY.md](../DEPLOY.md).
   - The file stores site credentials, database connection details and repository addresses used by the containers.
2. **Start the stack**
   ```bash
   docker compose up -d postgres redis
   docker compose up -d backend
   docker compose run --rm setup
   # once finished
   docker compose up -d
   ```
   The `setup` service installs the app and applies database migrations. It is safe to re‑run when updating an existing deployment.
3. **Update an existing deployment**
   ```bash
   docker compose run --rm setup
   docker compose restart backend
   ```

## Continuous Integration

GitHub Actions ensures code quality and successful builds:

- **Linters** – `.github/workflows/linter.yml` runs `pre-commit` hooks and Semgrep on pull requests.
- **Tests and deployment** – `.github/workflows/ci.yml` builds a bench environment, executes the test suite and, on pushes to the `develop` branch, deploys via SSH to the target server.

To reproduce the checks locally run:

```bash
pre-commit run --files <changed files>
```

