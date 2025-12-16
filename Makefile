SHELL := /bin/bash
BENCH_SITE ?= test_site
APP ?= ferum_custom
TEST_PATH ?= apps/$(APP)/$(APP)/tests
PYTHON ?= ./env/bin/python
PYTEST ?= ./env/bin/pytest
DOCKER_TAG ?= $(APP):local
DOCKERFILE ?= apps/$(APP)/Dockerfile
DOCKER_REGISTRY ?=
BOOTSTRAP_SITE ?= $(BENCH_SITE)
DOCKER_PLATFORM ?=

.PHONY: help
help:
	@echo "Common targets:"
	@echo "  make install          # install pre-commit hooks (dev hygiene)"
	@echo "  make lint             # run Ruff/Black/isort/ESLint/Prettier via pre-commit"
	@echo "  make format           # format Python/JS/CSS/MD in apps/ferum_custom"
	@echo "  make test [FILE=...]  # run pytest suite (or single file) for $(APP)"
	@echo "  make bench-test       # run bench test runner for $(APP) on $(BENCH_SITE)"
	@echo "  make ci               # lint + pytest"
	@echo "  make ci-bench         # lint + bench-test on $(BENCH_SITE)"
	@echo "  make migrate          # bench migrate on $(BENCH_SITE)"
	@echo "  make build-prod       # bench build --production"
	@echo "  make verify           # migrate then bench-test on $(BENCH_SITE)"
	@echo "  make docker-build     # build $(DOCKER_TAG) using $(DOCKERFILE)"
	@echo "  make docker-push      # push $(DOCKER_REGISTRY)$(DOCKER_TAG)"
	@echo "  make bootstrap-site   # ensure $(APP) is installed on $(BOOTSTRAP_SITE) and migrated"
	@echo "  make deploy           # docker-build (+platform) then docker-push"
	@echo "  make watch            # bench watch (asset rebuilds)"
	@echo "  make start            # bench start (dev services)"
	@echo "  make clean            # drop __pycache__/.pyc/.pytest_cache/htmlcov (keeps env/node_modules)"

.PHONY: install
install:
	pre-commit install --install-hooks

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: format
format:
	pre-commit run black isort prettier --all-files

.PHONY: ci
ci: lint test

.PHONY: ci-bench
ci-bench: lint bench-test

.PHONY: test
test:
	FRAPPE_STREAM_LOGGING=1 $(PYTEST) $(if $(FILE),$(TEST_PATH)/$(FILE),$(TEST_PATH)) $(PYTEST_OPTS)

.PHONY: bench-test
bench-test:
	FRAPPE_STREAM_LOGGING=1 bench --site $(BENCH_SITE) run-tests --app $(APP)

.PHONY: build-prod
build-prod:
	bench build --production

.PHONY: docker-build
docker-build:
	docker build $(if $(DOCKER_PLATFORM),--platform $(DOCKER_PLATFORM),) -f $(DOCKERFILE) -t $(DOCKER_TAG) .

.PHONY: docker-push
docker-push: docker-build
	docker tag $(DOCKER_TAG) $(DOCKER_REGISTRY)$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)$(DOCKER_TAG)

.PHONY: deploy
deploy: docker-build docker-push

.PHONY: migrate
migrate:
	bench --site $(BENCH_SITE) migrate

.PHONY: verify
verify: migrate bench-test

.PHONY: bootstrap-site
bootstrap-site:
	SITE=$(BOOTSTRAP_SITE) APP=$(APP) ./scripts/bootstrap_site.sh

.PHONY: watch
watch:
	bench watch

.PHONY: start
start:
	bench start

.PHONY: clean
clean:
	find . \
		-path "./.venv" -prune -o \
		-path "./env" -prune -o \
		-path "./node_modules" -prune -o \
		-path "./sites/assets" -prune -o \
		-path "./frappe-bench" -prune -o \
		-path "./build" -prune -o \
		\( -name "__pycache__" -o -name "*.pyc" -o -name ".pytest_cache" -o -name "htmlcov" \) \
		-print -exec rm -rf {} +
