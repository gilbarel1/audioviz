# AudioViz Architecture Documentation

## System Design

AudioViz is a real-time music visualizer that separates concerns between audio processing (Python) and graphics rendering (C) for optimal performance and maintainability.

### Design Principles

1. **Separation of concerns**: Python handles I/O-bound audio processing; C handles CPU-intensive rendering
2. **Language optimization**: Leverage Python's rich ecosystem (librosa, SciPy) and C's performance for graphics
3. **Low latency**: Shared memory IPC achieves <20ms end-to-end latency
4. **Testability**: Each component tested independently with unit and integration tests
5. **Modularity**: Pluggable visualizers, audio backends, window functions

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Audio File (MP3/WAV)                   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│              Python Audio Processor (pyviz/)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ AudioLoader  │→ │   Processor  │→ │  Transport   │   │
│  │  (librosa)   │  │  (SciPy FFT) │  │ (posix_ipc)  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────┬─────────────────────────────┘
                              │ Shared Memory (32KB buffer)
                              │ Semaphores (synchronization)
                              ▼
┌───────────────────────────────────────────────────────────┐
│               C Renderer (libviz/)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  ShmReader   │→ │   Renderer   │→ │  Visualizer  │   │
│  │   (POSIX)    │  │ (SDL3/OpenGL)│  │    (bars)    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │    Display    │
                      │   (60 FPS)    │
                      └───────────────┘
```

## Data Flow

### Processing Pipeline

1. **Audio Ingestion** (pyviz/audio.py)
   - Load file via librosa/soundfile/pydub
   - Decode to PCM float32 samples
   - Downsample to 44.1kHz mono
   - Stream in chunks with overlap

2. **Signal Processing** (pyviz/processor.py)
   - Apply Hann window to chunk (1024 samples)
   - Compute FFT via `scipy.fft.rfft`
   - Extract magnitude spectrum: `|X[k]|`
   - Normalize to [0, 1] range
   - Optional: smoothing with exponential decay

3. **IPC Transport** (pyviz/transport.py)
   - Serialize frame: [Header 64B][Magnitude 2KB][Phase 2KB]
   - Write to circular buffer slot: `frame_seq % 8`
   - Signal semaphore to consumer
   - Handle backpressure: drop old frames if buffer full

4. **Data Reception** (libviz/src/shm_reader.c)
   - Wait on semaphore (blocking with timeout)
   - Read from next slot in circular buffer
   - Validate magic number (0x56495A46)
   - Detect dropped frames (sequence gaps)

5. **Visualization** (libviz/src/visualizers/bars.c)
   - Map 512 FFT bins → 32 logarithmic bars
   - Apply smoothing and decay
   - Interpolate bar heights

6. **Rendering** (libviz/src/renderer.c)
   - Draw visualization to framebuffer
   - Maintain 60 FPS target (vsync or manual throttle)
   - Process window events

## Inter-Process Communication

### Shared Memory Protocol

**Layout:**
```
Total: 32KB (8 slots × 4096 bytes)

Slot structure:
┌────────────────────────────────────────┐
│ Header (64 bytes)                      │
├────────────────────────────────────────┤
│ Magic: 0x56495A46 (4B)                 │
│ Frame sequence: uint64 (8B)            │
│ Timestamp: uint64 µs (8B)              │
│ Sample rate: uint32 Hz (4B)            │
│ Bin count: uint32 (4B)                 │
│ Reserved: (36B)                        │
├────────────────────────────────────────┤
│ FFT Magnitude: float32[512] (2048B)    │
├────────────────────────────────────────┤
│ FFT Phase: float32[512] (2048B)        │
├────────────────────────────────────────┤
│ Padding (to 4096B)                     │
└────────────────────────────────────────┘
```

**Synchronization:**
- Semaphore `/audioviz_sem_write`: incremented by producer, decremented by consumer
- Circular buffer: write to `(seq % 8)`, read from oldest unread
- Backpressure: if semaphore value = 8 (buffer full), producer drops frames

**Why Shared Memory?**
- **Zero-copy**: No serialization overhead, direct memory access
- **Low latency**: <1ms write + <1ms read vs 2-5ms for sockets
- **Real-time**: Critical for <20ms glass-to-glass target
- **Trade-off**: Platform-specific (POSIX only), but best performance

**Alternatives considered:**
- **Unix domain sockets**: +2-3ms latency, simpler cross-platform (Windows named pipes)
- **Message queues**: Higher overhead, not suitable for real-time
- **C extension (ctypes/Cython)**: Tight coupling, harder to debug

## Module Responsibilities

### Python Components

**pyviz/audio.py**
- Detect available backend (librosa → soundfile → pydub)
- Load and decode audio files
- Resample to target sample rate
- Downsix stereo to mono (average channels)
- Stream chunks with configurable overlap
- Zero-pad short final chunks

**pyviz/processor.py**
- Create window functions (Hann, Hamming, Blackman)
- Apply window to audio chunks
- Compute real FFT via SciPy (efficient for real inputs)
- Extract magnitude and phase
- Normalize magnitude to [0, 1]
- Compute frequency bins for visualization
- Apply temporal smoothing between frames

**pyviz/transport.py**
- Create/attach POSIX shared memory segment
- Create/attach semaphores for synchronization
- Serialize frame header + FFT data
- Write to circular buffer slot
- Handle backpressure (drop frames when full)
- Cleanup resources on exit

**pyviz/cli.py**
- Parse command-line arguments
- Configure audio loader and processor
- Coordinate processing pipeline
- Throttle to real-time playback speed
- Report statistics (frames sent/dropped, FPS)

### C Components

**libviz/src/shm_reader.c**
- Attach to existing shared memory segment
- Open semaphore for synchronization
- Block on semaphore wait (with timeout)
- Read frame from circular buffer slot
- Validate magic number and sequence
- Detect dropped frames
- Track statistics

**libviz/src/renderer.c**
- Initialize SDL3 window and OpenGL context (stub in current version)
- Set up rendering pipeline
- Draw visualization to framebuffer
- Swap buffers (vsync or manual timing)
- Maintain target FPS
- Handle window events (close, resize)

**libviz/src/visualizers/bars.c**
- Map FFT bins to logarithmic frequency scale
- Aggregate bins into 32 bars
- Apply exponential smoothing (α=0.3)
- Apply decay to previous heights
- Track peak values with slower decay
- Provide bar heights for rendering

**libviz/src/main.c**
- Initialize all subsystems
- Set up signal handlers (SIGINT, SIGTERM)
- Run main event loop
- Coordinate reader and renderer
- Print periodic statistics
- Clean shutdown

## Non-Functional Requirements

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Audio decode latency | <5ms/frame | `time.time()` around `processor.process_chunk()` |
| FFT computation | <3ms/frame | SciPy FFTW backend |
| IPC write latency | <1ms/frame | Shared memory direct write |
| IPC read latency | <1ms/frame | Memory copy + validation |
| Render latency | <10ms/frame | Stub implementation (no actual GPU) |
| **Total latency** | **<20ms** | Audio input → visual output |
| Audio frame rate | 43 FPS | 44100 Hz ÷ 1024 samples |
| Renderer frame rate | 60 FPS | Vsync or manual throttle |

### Memory Usage

- Python process: ~50MB (librosa overhead + audio buffer)
- C process: <10MB (framebuffer + textures)
- Shared memory: 32KB (8 × 4KB slots)
- Total: ~60MB

### Throughput

- Audio: 44.1 kHz mono = 176 KB/s PCM
- FFT output: 512 floats × 4 bytes = 2 KB/frame
- Frame rate: 43 FPS → 86 KB/s FFT data
- IPC bandwidth: negligible (< 0.1 MB/s)

### Scalability Considerations

- **Higher frame rates**: Reduce FFT size (512 → 86 FPS)
- **Lower latency**: Reduce hop size (more overlap)
- **More frequency resolution**: Increase FFT size (2048 → 23 FPS)
- **Multiple visualizations**: Fork renderer process or multi-thread

### Error Handling

- **Audio file not found**: Validate path before loading
- **Unsupported format**: Try multiple backends, report failure
- **IPC creation failure**: Check permissions, existing resources
- **Buffer full**: Drop frames, log warning, continue
- **Validation failure**: Check magic number, skip corrupted frames
- **Renderer crash**: Python continues, renderer can reconnect

## Platform-Specific Notes

### Linux
- Full POSIX IPC support
- Install SDL3: `sudo apt-get install libsdl3-dev`
- Shared memory: `/dev/shm/audioviz_shm`
- Semaphores: `/dev/shm/sem.audioviz_sem_write`

### macOS
- Full POSIX IPC support
- Install SDL3: `brew install sdl3`
- Shared memory: kernel-managed
- Semaphores: kernel-managed

### Windows
- **No native POSIX IPC**
- Options:
  1. Use WSL2 (Linux subsystem)
  2. Implement Windows named pipes alternative
  3. Use Cygwin for POSIX compatibility
- Implementation notes in `docs/developer_guide.md`

## Future Enhancements

### Short-term
- [ ] Implement full SDL3 + OpenGL renderer
- [ ] Add more visualizers (waveform, spectrogram, circular)
- [ ] Support real-time audio input (microphone)
- [ ] Add configuration file (YAML/TOML)

### Medium-term
- [ ] Windows named pipes IPC implementation
- [ ] Plugin system for custom visualizers
- [ ] GPU acceleration (CUDA/OpenCL for FFT)
- [ ] Web-based remote viewer (WebSocket + Canvas)

### Long-term
- [ ] Multi-channel audio support (5.1, 7.1)
- [ ] Beat detection and rhythm analysis
- [ ] Music genre classification (ML model)
- [ ] VR/AR visualization output

## References

- **POSIX Shared Memory**: `man shm_overview`
- **POSIX Semaphores**: `man sem_overview`
- **SciPy FFT**: https://docs.scipy.org/doc/scipy/reference/fft.html
- **librosa**: https://librosa.org/doc/latest/index.html
- **SDL3**: https://wiki.libsdl.org/SDL3/FrontPage
- **OpenGL**: https://www.opengl.org/documentation/
