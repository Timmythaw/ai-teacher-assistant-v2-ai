.PHONY: help install format lint type-check test test-unit test-integration clean all pre-commit

help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies with uv"
	@echo "  make format          - Format code with black and ruff"
	@echo "  make lint            - Lint code with ruff"
	@echo "  make type-check      - Type check with mypy"
	@echo "  make test            - Run all tests with coverage"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make all             - Run format, lint, type-check, test"
	@echo "  make pre-commit      - Install pre-commit hooks"
	@echo "  make clean           - Remove cache and build files"

install:
	uv sync --all-extras

format:
	@echo "🎨 Formatting code with black..."
	uv run black src/ tests/
	@echo "🎨 Formatting code with ruff..."
	uv run ruff format src/ tests/
	@echo "📦 Sorting imports with ruff..."
	uv run ruff check --select I --fix src/ tests/

lint:
	@echo "🔍 Linting with ruff..."
	uv run ruff check src/ tests/

type-check:
	@echo "🔬 Type checking with mypy..."
	uv run mypy src/

test:
	@echo "🧪 Running all tests with coverage..."
	uv run pytest tests/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	uv run pytest tests/ -v -m unit

test-integration:
	@echo "🧪 Running integration tests..."
	uv run pytest tests/ -v -m integration

pre-commit:
	@echo "🪝 Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "✅ Pre-commit hooks installed!"

all: format lint type-check test
	@echo "✅ All checks passed!"

clean:
	@echo "🧹 Cleaning up..."
	rm -rf .mypy_cache .ruff_cache .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✨ Cleanup complete!"
