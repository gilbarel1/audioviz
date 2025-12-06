/**
 * Shared Memory Protocol Definition
 * 
 * Defines the binary layout for IPC between Python audio processor
 * and C renderer. This header is shared between both components.
 */

#ifndef SHM_PROTOCOL_H
#define SHM_PROTOCOL_H

#include <stdint.h>

// Protocol constants
#define MAGIC_NUMBER 0x56495A46  // "VIZF"
#define BUFFER_SLOTS 8
#define SLOT_SIZE 8192           // Increased to fit header + data
#define HEADER_SIZE 64
#define MAX_FFT_BINS 512

// Shared memory name
#define SHM_NAME "/audioviz_shm"
#define SEM_WRITE_NAME "/audioviz_sem_write"
#define SEM_READ_NAME "/audioviz_sem_read"

/**
 * Frame header structure (64 bytes total)
 * Little-endian byte order
 */
typedef struct {
    uint32_t magic;           // Magic number for validation (0x56495A46)
    uint64_t frame_sequence;  // Frame sequence number
    uint64_t timestamp_us;    // Timestamp in microseconds
    uint32_t sample_rate;     // Audio sample rate in Hz
    uint32_t bin_count;       // Number of FFT bins in this frame
    uint8_t  reserved[36];    // Reserved for future use
} __attribute__((packed)) FrameHeader;

/**
 * Complete frame structure
 * Layout: [FrameHeader][magnitude_bins][phase_bins][padding]
 */
typedef struct {
    FrameHeader header;
    float magnitude[MAX_FFT_BINS];  // FFT magnitude bins (normalized 0-1)
    float phase[MAX_FFT_BINS];      // FFT phase in radians (optional)
    uint8_t padding[SLOT_SIZE - HEADER_SIZE - (2 * MAX_FFT_BINS * sizeof(float))];
} __attribute__((packed)) Frame;

// Compile-time assertions
_Static_assert(sizeof(FrameHeader) == HEADER_SIZE, "FrameHeader must be 64 bytes");
_Static_assert(sizeof(Frame) == SLOT_SIZE, "Frame must match slot size");

#endif // SHM_PROTOCOL_H
