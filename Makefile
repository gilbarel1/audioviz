# Makefile for AudioViz - Music Visualizer Project
# 
# Cross-platform build automation
# Note: Windows users should use Git Bash, WSL, or install GNU Make

.PHONY: help dev-install build-c build-python test clean run mock-audio venv

PYTHON := python3
CMAKE := cmake
BUILD_DIR := libviz/build
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

help:
	@echo "AudioViz - Music Visualizer Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  dev-install   - Set up development environment (Python + C)"
	@echo "  build-python  - Build Python package (editable install)"
	@echo "  build-c       - Build C renderer"
	@echo "  test          - Run all tests"
	@echo "  test-python   - Run Python tests only"
	@echo "  test-c        - Run C tests only"
	@echo "  clean         - Clean build artifacts"
	@echo "  run           - Run the complete system (requires audio file)"
	@echo "  mock-audio    - Generate mock audio file for testing"
	@echo ""

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
		echo "✓ Virtual environment created at $(VENV)"; \
	fi

dev-install: venv build-python build-c
	@echo ""
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "Quick start:"
	@echo "  1. Activate venv: source $(VENV)/bin/activate"
	@echo "  2. Generate test audio: make mock-audio"
	@echo "  3. Run processor: python -m pyviz.cli mock_audio.wav"
	@echo "  4. Run renderer: ./$(BUILD_DIR)/audioviz_renderer"
	@echo ""

build-python: $(VENV)/bin/pip
	@echo "Building Python package..."
	$(PIP) install -e . --no-deps
	$(PIP) install -r requirements.txt
	@echo "✓ Python package installed"

$(VENV)/bin/pip:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "✓ Virtual environment created"

build-c:
	@echo "Building C renderer..."
	mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && $(CMAKE) .. && $(CMAKE) --build .
	@echo "✓ C renderer built: $(BUILD_DIR)/audioviz_renderer"

test: test-python test-c

test-python: venv
	@echo "Running Python tests..."
	$(PYTHON_VENV) -m pytest tests/pyviz/ tests/integration/ -v

test-c:
	@echo "Running C tests..."
	@if [ -f "$(BUILD_DIR)/test_shm" ]; then \
		$(BUILD_DIR)/test_shm; \
	else \
		echo "C tests not built. Run 'make build-c' first."; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(BUILD_DIR)
	rm -rf $(VENV)
	rm -rf pyviz.egg-info
	rm -rf pyviz/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

mock-audio: venv
	@echo "Generating mock audio file..."
	$(PYTHON_VENV) tools/mock_audio_gen.py

run: venv
	@echo "Starting AudioViz system..."
	@echo "Terminal 1: $(PYTHON_VENV) -m pyviz.cli mock_audio.wav"
	@echo "Terminal 2: ./$(BUILD_DIR)/audioviz_renderer"