# Makefile for Invasive Species Tracker

.PHONY: help install test clean lint format run

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Run linting"
	@echo "  make format    - Format code"
	@echo "  make clean     - Clean up temporary files"
	@echo "  make run       - Run the application"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf dist/ build/ *.egg-info
	rm -rf htmlcov/ .coverage

run:
	python -m src.main