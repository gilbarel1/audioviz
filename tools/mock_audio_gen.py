"""
Mock audio generator for testing without real audio files.

Generates synthetic audio signals for development and testing.
"""

import numpy as np
import argparse


def generate_sine_sweep(duration=5.0, sample_rate=44100, freq_start=100, freq_end=8000):
    """
    Generate a logarithmic sine sweep from freq_start to freq_end.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        freq_start: Starting frequency in Hz
        freq_end: Ending frequency in Hz
        
    Returns:
        Audio samples as float32 array
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Logarithmic frequency sweep
    freq = np.logspace(np.log10(freq_start), np.log10(freq_end), len(t))
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    
    audio = np.sin(phase).astype(np.float32)
    
    # Apply fade in/out
    fade_samples = int(0.1 * sample_rate)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    
    audio[:fade_samples] *= fade_in
    audio[-fade_samples:] *= fade_out
    
    return audio


def generate_white_noise(duration=5.0, sample_rate=44100, amplitude=0.3):
    """
    Generate white noise.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude factor (0-1)
        
    Returns:
        Audio samples as float32 array
    """
    num_samples = int(sample_rate * duration)
    audio = np.random.randn(num_samples).astype(np.float32) * amplitude
    return audio


def generate_chord(duration=5.0, sample_rate=44100, frequencies=[261.63, 329.63, 392.00]):
    """
    Generate a chord (multiple simultaneous tones).
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        frequencies: List of frequencies in Hz (default: C major chord)
        
    Returns:
        Audio samples as float32 array
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.zeros_like(t, dtype=np.float32)
    
    for freq in frequencies:
        audio += np.sin(2 * np.pi * freq * t)
    
    # Normalize
    audio = audio / len(frequencies)
    
    return audio.astype(np.float32)


def generate_rhythm(duration=5.0, sample_rate=44100, bpm=120):
    """
    Generate a rhythmic pattern (kick drum simulation).
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        bpm: Beats per minute
        
    Returns:
        Audio samples as float32 array
    """
    num_samples = int(sample_rate * duration)
    audio = np.zeros(num_samples, dtype=np.float32)
    
    beat_interval = int(60.0 / bpm * sample_rate)
    kick_duration = int(0.1 * sample_rate)
    
    for i in range(0, num_samples, beat_interval):
        if i + kick_duration < num_samples:
            # Simple kick drum: decaying sine
            t = np.linspace(0, 0.1, kick_duration)
            freq = 60 * np.exp(-20 * t)  # Pitch drop
            kick = np.sin(2 * np.pi * freq * t) * np.exp(-10 * t)
            audio[i:i+kick_duration] += kick
    
    return audio


def save_wav(audio, filename, sample_rate=44100):
    """Save audio to WAV file."""
    import wave
    import struct
    
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    print(f"Saved: {filename}")


def main():
    parser = argparse.ArgumentParser(description='Generate mock audio for testing')
    parser.add_argument(
        'type',
        choices=['sine_sweep', 'white_noise', 'chord', 'rhythm'],
        help='Type of audio to generate'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=5.0,
        help='Duration in seconds'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='mock_audio.wav',
        help='Output filename'
    )
    parser.add_argument(
        '--sample-rate',
        type=int,
        default=44100,
        help='Sample rate'
    )
    
    args = parser.parse_args()
    
    if args.type == 'sine_sweep':
        audio = generate_sine_sweep(args.duration, args.sample_rate)
    elif args.type == 'white_noise':
        audio = generate_white_noise(args.duration, args.sample_rate)
    elif args.type == 'chord':
        audio = generate_chord(args.duration, args.sample_rate)
    elif args.type == 'rhythm':
        audio = generate_rhythm(args.duration, args.sample_rate)
    
    save_wav(audio, args.output, args.sample_rate)


if __name__ == '__main__':
    main()
