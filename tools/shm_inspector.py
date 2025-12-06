"""
Shared memory inspector - Debug tool to dump SHM contents.

Usage: python shm_inspector.py [--shm-name NAME] [--continuous]
"""

import argparse
import struct
import time
from pyviz import transport
from pyviz.config import SHM_NAME, BUFFER_SLOTS, SLOT_SIZE, HEADER_SIZE, MAGIC_NUMBER


def inspect_shared_memory(shm_name, continuous=False, interval=1.0):
    """Inspect and dump shared memory contents."""
    if not transport.POSIX_IPC_AVAILABLE:
        print("Error: posix_ipc not available")
        return
    
    import posix_ipc
    import mmap
    
    try:
        # Attach to existing shared memory
        shm = posix_ipc.SharedMemory(shm_name)
        mapfile = mmap.mmap(shm.fd, BUFFER_SLOTS * SLOT_SIZE)
        
        print(f"Connected to shared memory: {shm_name}")
        print(f"Total size: {BUFFER_SLOTS * SLOT_SIZE} bytes ({BUFFER_SLOTS} slots)\n")
        
        while True:
            print("=" * 80)
            print(f"Timestamp: {time.strftime('%H:%M:%S')}")
            print("=" * 80)
            
            for slot_idx in range(BUFFER_SLOTS):
                offset = slot_idx * SLOT_SIZE
                mapfile.seek(offset)
                header_bytes = mapfile.read(HEADER_SIZE)
                
                if len(header_bytes) < HEADER_SIZE:
                    print(f"Slot {slot_idx}: [EMPTY]")
                    continue
                
                # Parse header
                magic, frame_seq, timestamp_us, sample_rate, bin_count = struct.unpack(
                    "<IQQIIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", header_bytes
                )
                
                if magic != MAGIC_NUMBER:
                    print(f"Slot {slot_idx}: [INVALID MAGIC: 0x{magic:08X}]")
                    continue
                
                # Read first few magnitude bins
                mapfile.seek(offset + HEADER_SIZE)
                mag_bytes = mapfile.read(20)  # First 5 floats
                mags = struct.unpack("<5f", mag_bytes)
                
                print(f"Slot {slot_idx}:")
                print(f"  Frame: {frame_seq}")
                print(f"  Timestamp: {timestamp_us} µs")
                print(f"  Sample rate: {sample_rate} Hz")
                print(f"  Bin count: {bin_count}")
                print(f"  First bins: {[f'{m:.3f}' for m in mags]}")
            
            if not continuous:
                break
            
            print(f"\nRefreshing in {interval}s... (Ctrl+C to exit)\n")
            time.sleep(interval)
        
    except posix_ipc.ExistentialError:
        print(f"Error: Shared memory '{shm_name}' does not exist")
        print("Make sure the audio processor is running.")
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            mapfile.close()
            shm.close_fd()
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description='Inspect shared memory contents')
    parser.add_argument(
        '--shm-name',
        type=str,
        default=SHM_NAME,
        help=f'Shared memory name (default: {SHM_NAME})'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Continuously refresh display'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Refresh interval in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    inspect_shared_memory(args.shm_name, args.continuous, args.interval)


if __name__ == '__main__':
    main()
