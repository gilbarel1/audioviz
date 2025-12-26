import numpy as np
import time
# Import the C++ extension (built from libaudioviz)
import libaudioviz

#this is a dummy function!!
## TODO - implement a real one...
def get_next_audio_chunk(size=1024):
    """Generates random white noise to simulate audio input."""
    # Create random float data between -1.0 and 1.0
    return np.random.uniform(-1.0, 1.0, size).astype(np.float32)

def main():
    # 1. Initialize C++ Renderer
    renderer = libaudioviz.Renderer(800, 600)
    renderer.initialize_window()

    print("Starting render loop... (Press Ctrl+C to stop)")

    try:
        # 2. Loop to simulate processing frames
        while True:
            # A. Get dummy audio data
            audio_chunk = get_next_audio_chunk()
            
            # B. Perform FFT in Python (Real Audio -> Complex Frequencies)
            fft_data = np.fft.fft(audio_chunk)
            
            # This is the step where Python hands off data to C++
            renderer.render_frame(fft_data.astype(np.complex64))
            
            
            # Slow down slightly
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()