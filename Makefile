# Makefile for local-pdf-chat
.PHONY: help install run test lint format clean

# Default target
help:
	@echo "local-pdf-chat - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     - Install dependencies in venv"
	@echo "  make models      - Pull required Ollama models"
	@echo ""
	@echo "Development:"
	@echo "  make run         - Run Streamlit app"
	@echo "  make ollama      - Start Ollama with keep-alive"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters (ruff, black)"
	@echo "  make format      - Auto-format code"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       - Remove cache and build files"

# Create and setup virtual environment
venv:
	python3 -m venv venv

install: venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt

# Pull required models
models:
	ollama pull nomic-embed-text
	ollama pull llama3.1:8b

# Run the app
run:
	venv/bin/streamlit run app.py

# Start Ollama with persistent models
ollama:
	OLLAMA_KEEP_ALIVE=-1 ollama serve

# Run tests
test:
	venv/bin/pytest tests/ -v

# Linting
lint:
	venv/bin/ruff check .
	venv/bin/black --check --diff .

# Auto-format
format:
	venv/bin/black .
	venv/bin/ruff check --fix .

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build *.egg-info 2>/dev/null || true

# Full setup for new developers
setup: install models
	@echo "Setup complete! Run 'make ollama' in one terminal and 'make run' in another."
	@echo "Project: local-pdf-chat"