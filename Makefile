.PHONY: setup format lint check test run clean build build-dir build-clean

setup:
	uv sync

format:
	uv run ruff format
	uv run ruff check --fix

lint:
	uv run ruff format --check
	uv run ruff check

check: lint

test:
	uv run pytest -v tests/

run:
	uv run labelvid

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Build executable (single file)
build:
	pip install pyinstaller
	python build_exe.py

# Build executable (directory mode, faster startup)
build-dir:
	pip install pyinstaller
	python build_exe.py --onedir

# Clean build artifacts and rebuild
build-clean:
	pip install pyinstaller
	python build_exe.py --clean
