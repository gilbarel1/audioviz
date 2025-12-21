# audioviz

Audio visualization with Python FFT processing.

## Overview

This project loads audio files and computes Short-Time Fourier Transform (STFT) to analyze frequency content over time.

## Quick Start

### Using Docker (Recommended)

```bash
make run
make attach
make deploy
```

### Usage

```bash
# Analyze an audio file
audioviz path/to/audio.wav

# With custom FFT window size
audioviz path/to/audio.wav --nperseg 2048
```

### Running Tests

```bash
make test
```

## Project Structure

```
audioviz/
├── audioviz/           # Python package
│   ├── __init__.py
│   ├── __main__.py     # Entry point for python -m audioviz
│   ├── audio.py        # Audio loading with soundfile
│   ├── cli.py          # Command-line interface
│   └── stft.py         # STFT computation with SciPy
├── tests/              # Test suite
├── deployment/         # Docker configuration
├── Makefile            # Build automation
└── pyproject.toml      # Package configuration
```
