"""Pytest configuration and shared fixtures."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "audio_params: mark test with audio parameters")


@pytest.fixture
def sample_rate() -> int:
    """Audio sample rate in Hz."""
    return 44100


@pytest.fixture
def duration_sec() -> float:
    """Audio duration in seconds."""
    return 0.5


@pytest.fixture
def frequency_hz() -> int:
    """Tone frequency in Hz."""
    return 440


@pytest.fixture
def chunk_size() -> int:
    """Streaming chunk size in frames."""
    return 4096


@pytest.fixture
def stereo_channels() -> int:
    """Number of stereo channels."""
    return 2
