"""
Configuration constants for PyViz audio processing.
"""

# Audio processing parameters
DEFAULT_SAMPLE_RATE = 44100  # Hz
DEFAULT_FFT_SIZE = 1024  # samples
DEFAULT_HOP_SIZE = 512  # 50% overlap
DEFAULT_WINDOW = "hann"  # Hann window for FFT

# IPC parameters
SHM_NAME = "/audioviz_shm"
SEM_WRITE_NAME = "/audioviz_sem_write"
SEM_READ_NAME = "/audioviz_sem_read"
BUFFER_SLOTS = 8
SLOT_SIZE = 8192  # bytes (increased to fit header + FFT data)
HEADER_SIZE = 64  # bytes
MAX_FFT_BINS = 512

# Frame rate
DEFAULT_TARGET_FPS = 43  # ~44100 / 1024

# Magic number for protocol validation
MAGIC_NUMBER = 0x56495A46  # "VIZF" in hex

# Data format
ENDIANNESS = "little"
