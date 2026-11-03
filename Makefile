.DEFAULT_GOAL := help
.PHONY: help install run test preview clean

help: ## Show this help
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

install: ## Install dependencies, including test tools
	uv sync

run: ## Start the bot (needs .env)
	uv run src/main.py

test: ## Run the tests
	uv run pytest

preview: ## Print the boards from config.toml with mock data, without Discord
	uv run src/preview.py

clean: ## Remove caches
	uv run python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*') if p.is_dir() and p.name in ('__pycache__', '.pytest_cache') and '.venv' not in p.parts]"
