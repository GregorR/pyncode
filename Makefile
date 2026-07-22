# Makefile for pyncode

.PHONY: install test lint clean help

install:
	@echo "Installing pyncode and dependencies..."
	pip install -e .

install-dev:
	@echo "Installing pyncode with development dependencies..."
	pip install -e ".[dev]"

test:
	@echo "Running tests..."
	python -m pytest test_pyncode.py -v

test-coverage:
	@echo "Running tests with coverage..."
	python -m pytest test_pyncode.py -v --cov=pyncode --cov-report=html

lint:
	@echo "Running linter..."
	flake8 pyncode.py test_pyncode.py

format:
	@echo "Formatting code..."
	black pyncode.py test_pyncode.py

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf dist/
	rm -rf build/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

help:
	@echo "Available targets:"
	@echo "  install       - Install pyncode and dependencies"
	@echo "  install-dev   - Install with development dependencies"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run linter"
	@echo "  format        - Format code with black"
	@echo "  clean         - Clean up generated files"
	@echo "  help          - Show this help message"
