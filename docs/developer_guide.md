# AudioViz Developer Guide

Complete guide for developers working on AudioViz.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Building & Running](#building--running)
4. [Testing Strategy](#testing-strategy)
5. [Debugging](#debugging)
6. [Adding Features](#adding-features)
7. [Performance Tuning](#performance-tuning)
8. [Platform-Specific Notes](#platform-specific-notes)

---

## Development Setup

### Prerequisites

**Required:**
- Python 3.8+ with pip
- C compiler (GCC 7+ or Clang 9+)
- CMake 3.15+
- Git

**Optional:**
- SDL3 development libraries (for full graphics)
- OpenGL development libraries
- VS Code with recommended extensions

### One-Command Setup

```bash
git clone https://github.com/gilbarel1/audioviz.git
cd audioviz
make dev-install
```

### Manual Setup

**Python environment:**
```bash
# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .  # Editable install
```

**C renderer:**
```bash
mkdir libviz/build
cd libviz/build
cmake ..
cmake --build .
```

### IDE Configuration

**VS Code (recommended):**
```bash
# Open workspace
code .

# Recommended extensions installed automatically via .devcontainer
# - ms-python.python
# - ms-python.vscode-pylance
# - ms-vscode.cpptools
# - ms-vscode.cmake-tools
```

**Settings:**
- Python interpreter: `.venv/bin/python`
- C/C++ config: Uses `CMakeLists.txt`
- Format on save: enabled (Black for Python)

---

## Project Structure

### Directory Layout

```
audioviz/
├── pyviz/               # Python audio processing package
│   ├── __init__.py
│   ├── audio.py         # Audio loading (150 lines)
│   ├── processor.py     # FFT processing (120 lines)
│   ├── transport.py     # IPC transport (200 lines)
│   ├── cli.py           # Command-line interface (150 lines)
│   └── config.py        # Configuration constants (30 lines)
│
├── libviz/              # C rendering tier
│   ├── src/
│   │   ├── main.c       # Entry point (150 lines)
│   │   ├── shm_reader.c # IPC reader (200 lines)
│   │   ├── renderer.c   # Graphics stub (120 lines)
│   │   └── visualizers/
│   │       ├── bars.c   # Frequency bars (150 lines)
│   │       └── bars.h
│   ├── bindings/
│   │   └── shm_protocol.h  # Shared protocol (50 lines)
│   └── CMakeLists.txt
│
├── tests/               # Test suite
│   ├── conftest.py      # Shared fixtures
│   ├── pyviz/           # Python unit tests
│   │   ├── test_audio.py
│   │   ├── test_processor.py
│   │   └── test_transport.py
│   ├── libviz/          # C unit tests
│   │   └── test_shm.c
│   └── integration/     # End-to-end tests
│       └── test_e2e.py
│
├── tools/               # Development utilities
│   ├── mock_audio_gen.py   # Synthetic audio (150 lines)
│   └── shm_inspector.py    # Debug tool (120 lines)
│
├── docs/                # Documentation
│   ├── architecture.md  # System architecture
│   └── developer_guide.md  # This file
│
├── Makefile             # Build automation (100 lines)
├── pyproject.toml       # Python package metadata
├── requirements.txt     # Python dependencies
└── README.md            # User documentation
```

### Key Files

**Entry Points:**
- `pyviz/cli.py:main()` - Python audio processor CLI
- `libviz/src/main.c:main()` - C renderer executable

**Core Logic:**
- `pyviz/processor.py:SignalProcessor.process_chunk()` - FFT computation
- `libviz/src/shm_reader.c:shm_reader_read_frame()` - IPC receive
- `libviz/src/renderer.c:renderer_render_frame()` - Visualization

**Protocol:**
- `libviz/bindings/shm_protocol.h` - Shared between Python and C

---

## Building & Running

### Build Commands

```bash
# Full development setup
make dev-install

# Build only Python
make build-python

# Build only C
make build-c

# Clean all builds
make clean

# Format code
make format

# Lint code
make lint
```

### Running the System

**Terminal 1 - Audio Processor:**
```bash
# Generate test audio first
make mock-audio

# Run processor
python -m pyviz.cli mock_audio.wav --verbose

# Options:
#   --fft-size 1024       # FFT window size
#   --hop-size 512        # Overlap
#   --window hann         # Window function
#   --sample-rate 44100   # Target sample rate
```

**Terminal 2 - Renderer:**
```bash
./libviz/build/audioviz_renderer

# No command-line options yet (configure in main.c)
```

**Stop both:**
Press `Ctrl+C` in each terminal.

### Simulating Audio Input

**Generate synthetic audio:**
```bash
# Sine sweep (100 Hz → 8 kHz)
python tools/mock_audio_gen.py sine_sweep --duration 10 --output sweep.wav

# White noise
python tools/mock_audio_gen.py white_noise --duration 5 --output noise.wav

# Musical chord (C major)
python tools/mock_audio_gen.py chord --duration 8 --output chord.wav

# Rhythmic pattern (120 BPM kick drum)
python tools/mock_audio_gen.py rhythm --duration 10 --output rhythm.wav
```

---

## Testing Strategy

### Python Tests

**Run all Python tests:**
```bash
make test-python
# or
pytest tests/pyviz/ -v
```

**Run specific test file:**
```bash
pytest tests/pyviz/test_processor.py -v
```

**Run with coverage:**
```bash
pytest tests/pyviz/ --cov=pyviz --cov-report=html
# View: open htmlcov/index.html
```

**Key test files:**
- `test_audio.py` - Audio loading, chunking, resampling
- `test_processor.py` - FFT correctness, normalization, windowing
- `test_transport.py` - IPC write, backpressure, serialization

### C Tests

**Compile and run:**
```bash
cd tests/libviz
gcc -o test_shm test_shm.c ../../libviz/src/shm_reader.c \
    -I../../libviz/src -I../../libviz/bindings -lrt -lpthread -lm
./test_shm
```

**What to test:**
- Frame header size validation
- Magic number correctness
- Endianness handling
- Semaphore operations

### Integration Tests

**End-to-end pipeline:**
```bash
pytest tests/integration/test_e2e.py -v
```

**Tests:**
- Full pipeline: audio → FFT → IPC → validate
- Performance: latency < 5ms per frame
- Backpressure: buffer full handling

### Performance Benchmarks

**Measure processing latency:**
```python
import time
from pyviz.processor import SignalProcessor

processor = SignalProcessor(fft_size=1024)
chunk = np.random.randn(1024)

start = time.perf_counter()
magnitude, _ = processor.process_chunk(chunk)
elapsed = time.perf_counter() - start

print(f"FFT latency: {elapsed*1000:.3f} ms")  # Target: <5ms
```

---

## Debugging

### Debug Tools

**1. Shared Memory Inspector**

View live IPC data:
```bash
# One-time snapshot
python tools/shm_inspector.py

# Continuous monitoring
python tools/shm_inspector.py --continuous --interval 0.5
```

Output shows:
- Frame sequence numbers
- Timestamps
- Sample rates
- First few FFT bins

**2. Python Logging**

Enable verbose logging:
```bash
python -m pyviz.cli audio.wav --verbose
```

Or in code:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**3. GDB for C Debugging**

```bash
gdb ./libviz/build/audioviz_renderer
(gdb) break shm_reader_read_frame
(gdb) run
(gdb) print frame.header.frame_sequence
```

### Common Issues

**"posix_ipc not available"**
```bash
# Install on Linux/macOS
pip install posix-ipc

# Windows: use WSL2
wsl
```

**"Shared memory does not exist"**
```bash
# Clean stale resources
make cleanup-ipc

# Or manually
python -m pyviz.cli --cleanup

# Check existing segments
ls -la /dev/shm/ | grep audioviz
```

**"Dropped frames" warnings**
- Renderer too slow to consume
- Increase `BUFFER_SLOTS` in `config.py`
- Reduce FFT size (lower latency, less data)

**Build errors (C)**
```bash
# Check CMake version
cmake --version  # Need 3.15+

# Check compiler
gcc --version    # Need GCC 7+

# Clean and rebuild
make clean
make build-c
```

**Import errors (Python)**
```bash
# Ensure editable install
pip install -e .

# Check sys.path
python -c "import sys; print('\n'.join(sys.path))"
```

---

## Adding Features

### New Visualizer (C)

**1. Create visualizer file:**

```c
// libviz/src/visualizers/waveform.c
#include "waveform.h"

typedef struct {
    float history[1000];
    int history_idx;
} WaveformVisualizer;

WaveformVisualizer* waveform_create() {
    WaveformVisualizer* viz = calloc(1, sizeof(WaveformVisualizer));
    return viz;
}

void waveform_update(WaveformVisualizer* viz, const float* bins, int count) {
    // Store recent values for waveform display
    viz->history[viz->history_idx++] = bins[0];
    if (viz->history_idx >= 1000) viz->history_idx = 0;
}

void waveform_destroy(WaveformVisualizer* viz) {
    free(viz);
}
```

**2. Add header:**

```c
// libviz/src/visualizers/waveform.h
#ifndef WAVEFORM_H
#define WAVEFORM_H

typedef struct WaveformVisualizer WaveformVisualizer;

WaveformVisualizer* waveform_create();
void waveform_update(WaveformVisualizer* viz, const float* bins, int count);
void waveform_destroy(WaveformVisualizer* viz);

#endif
```

**3. Register in main.c:**

```c
#include "visualizers/waveform.h"

// In main():
WaveformVisualizer* waveform = waveform_create();

// In loop:
waveform_update(waveform, frame.magnitude, frame.header.bin_count);

// Cleanup:
waveform_destroy(waveform);
```

**4. Update CMakeLists.txt:**

```cmake
set(SOURCES
    src/main.c
    src/shm_reader.c
    src/renderer.c
    src/visualizers/bars.c
    src/visualizers/waveform.c  # Add this
)
```

**5. Rebuild:**
```bash
make build-c
```

### New Audio Backend (Python)

**Add to `pyviz/audio.py`:**

```python
def _load_new_backend(self, filepath: str) -> Tuple[np.ndarray, int]:
    """Load using new backend."""
    import new_audio_library
    
    audio = new_audio_library.load(filepath)
    samples = audio.to_numpy()
    sample_rate = audio.sample_rate
    
    # Convert to mono if needed
    if samples.ndim > 1:
        samples = np.mean(samples, axis=1)
    
    return samples, sample_rate
```

**Update `_detect_backend()`:**

```python
def _detect_backend(self) -> str:
    try:
        import new_audio_library
        return "new_backend"
    except ImportError:
        pass
    # ... existing backends
```

### Configuration Options

**Add to `pyviz/config.py`:**

```python
# New feature configuration
ENABLE_PHASE_OUTPUT = False
MAX_HISTORY_FRAMES = 100
COLOR_SCHEME = "rainbow"
```

**Use in code:**

```python
from .config import ENABLE_PHASE_OUTPUT

if ENABLE_PHASE_OUTPUT:
    magnitude, phase = processor.process_chunk(chunk, return_phase=True)
    transport.write_frame(magnitude, sample_rate, phase=phase)
```

---

## Performance Tuning

### Python Optimizations

**1. Use NumPy operations (vectorized):**
```python
# Good
magnitude = np.abs(fft_result) / (fft_size / 2)

# Bad (loop)
magnitude = np.array([abs(x) / (fft_size/2) for x in fft_result])
```

**2. Pre-allocate arrays:**
```python
# Good
window = np.hanning(fft_size)  # Once
windowed = chunk * window       # Reuse

# Bad
windowed = chunk * np.hanning(fft_size)  # Every frame
```

**3. Profile hot paths:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
for chunk in loader.stream_chunks(audio, 1024, 512):
    processor.process_chunk(chunk)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)
```

### C Optimizations

**1. Minimize memory copies:**
```c
// Good: direct pointer access
memcpy(frame, (uint8_t*)shm_ptr + offset, SLOT_SIZE);

// Bad: intermediate buffer
uint8_t temp[SLOT_SIZE];
memcpy(temp, (uint8_t*)shm_ptr + offset, SLOT_SIZE);
memcpy(frame, temp, SLOT_SIZE);
```

**2. Use compiler optimizations:**
```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
# Enables -O3 -DNDEBUG
```

**3. Profile with perf (Linux):**
```bash
perf record ./libviz/build/audioviz_renderer
perf report
```

### FFT Size Trade-offs

| FFT Size | Latency (ms) @ 44.1kHz | Frequency Resolution | Frame Rate |
|----------|------------------------|----------------------|------------|
| 512 | 11.6 | 86 Hz/bin | 86 FPS |
| 1024 | 23.2 | 43 Hz/bin | 43 FPS |
| 2048 | 46.4 | 21.5 Hz/bin | 21.5 FPS |

**Recommendation:** Start with 1024, adjust based on use case.

---

## Platform-Specific Notes

### Linux

**Install dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential cmake python3-dev libsdl3-dev

# Fedora/RHEL
sudo dnf install gcc gcc-c++ cmake python3-devel SDL3-devel
```

**Shared memory location:**
```bash
ls -la /dev/shm/audioviz_shm
```

### macOS

**Install dependencies:**
```bash
brew install cmake sdl3
```

**Xcode command-line tools:**
```bash
xcode-select --install
```

### Windows

**Option 1: WSL2 (Recommended)**
```powershell
wsl --install
wsl
# Now in Linux environment, follow Linux instructions
```

**Option 2: Native (Limited)**
- `posix_ipc` not available
- Need to implement Windows named pipes alternative
- See `docs/windows_ipc.md` (TODO)

**Option 3: Cygwin**
```bash
# Install Cygwin with GCC, CMake, Python
# Follow Linux instructions
```

---

## Contributing

### Code Style

**Python:**
- PEP 8 compliant
- Line length: 100 characters
- Format with Black: `make format`
- Lint with flake8: `make lint`
- Type hints recommended

**C:**
- K&R style bracing
- 4-space indentation
- Snake_case for functions and variables
- PascalCase for structs/types

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-visualizer

# Make changes, commit atomically
git add libviz/src/visualizers/new.c
git commit -m "Add new visualizer: <name>"

# Push and create PR
git push origin feature/new-visualizer
```

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted (`make format`)
- [ ] All tests pass (`make test`)
- [ ] No lint errors (`make lint`)
- [ ] PR description explains changes

---

## Resources

**Documentation:**
- [Architecture](architecture.md) - System design
- [README](../README.md) - User guide

**External:**
- [SciPy FFT Tutorial](https://docs.scipy.org/doc/scipy/tutorial/fft.html)
- [librosa Documentation](https://librosa.org/doc/latest/index.html)
- [POSIX IPC](https://man7.org/linux/man-pages/man7/shm_overview.7.html)
- [SDL3 Wiki](https://wiki.libsdl.org/SDL3/FrontPage)

**Community:**
- [GitHub Issues](https://github.com/gilbarel1/audioviz/issues)
- [Discussions](https://github.com/gilbarel1/audioviz/discussions)
