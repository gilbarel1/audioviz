/**
 * Shared Memory Reader Implementation
 */

#include "shm_reader.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <semaphore.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>

struct ShmReader {
    int shm_fd;
    void* shm_ptr;
    size_t shm_size;
    sem_t* sem_write;
    
    uint64_t frames_read;
    uint64_t frames_dropped;
    uint64_t last_sequence;
};

ShmReader* shm_reader_init(const char* shm_name, bool create) {
    ShmReader* reader = calloc(1, sizeof(ShmReader));
    if (!reader) {
        perror("calloc");
        return NULL;
    }
    
    reader->shm_size = BUFFER_SLOTS * SLOT_SIZE;
    reader->last_sequence = 0;
    
    // Open/create shared memory
    int flags = create ? (O_RDWR | O_CREAT) : O_RDWR;
    mode_t mode = S_IRUSR | S_IWUSR;
    
    reader->shm_fd = shm_open(shm_name, flags, mode);
    if (reader->shm_fd == -1) {
        perror("shm_open");
        free(reader);
        return NULL;
    }
    
    // Set size if creating
    if (create) {
        if (ftruncate(reader->shm_fd, reader->shm_size) == -1) {
            perror("ftruncate");
            close(reader->shm_fd);
            free(reader);
            return NULL;
        }
    }
    
    // Map shared memory
    reader->shm_ptr = mmap(NULL, reader->shm_size, PROT_READ | PROT_WRITE,
                           MAP_SHARED, reader->shm_fd, 0);
    if (reader->shm_ptr == MAP_FAILED) {
        perror("mmap");
        close(reader->shm_fd);
        free(reader);
        return NULL;
    }
    
    // Open semaphore
    int sem_flags = create ? (O_CREAT) : 0;
    reader->sem_write = sem_open(SEM_WRITE_NAME, sem_flags, mode, 0);
    if (reader->sem_write == SEM_FAILED) {
        perror("sem_open");
        munmap(reader->shm_ptr, reader->shm_size);
        close(reader->shm_fd);
        free(reader);
        return NULL;
    }
    
    printf("ShmReader: Initialized (create=%d, size=%zu bytes)\n", 
           create, reader->shm_size);
    
    return reader;
}

bool shm_reader_read_frame(ShmReader* reader, Frame* frame, int timeout_ms) {
    if (!reader || !frame) {
        return false;
    }
    
    // Wait for data
    struct timespec ts;
    if (timeout_ms > 0) {
        clock_gettime(CLOCK_REALTIME, &ts);
        ts.tv_sec += timeout_ms / 1000;
        ts.tv_nsec += (timeout_ms % 1000) * 1000000;
        if (ts.tv_nsec >= 1000000000) {
            ts.tv_sec += 1;
            ts.tv_nsec -= 1000000000;
        }
        
        if (sem_timedwait(reader->sem_write, &ts) == -1) {
            if (errno == ETIMEDOUT) {
                return false;
            }
            perror("sem_timedwait");
            return false;
        }
    } else {
        if (sem_wait(reader->sem_write) == -1) {
            perror("sem_wait");
            return false;
        }
    }
    
    // Determine which slot to read (oldest unread)
    // For simplicity, we read based on semaphore signaling
    // The producer writes to (frame_seq % BUFFER_SLOTS)
    // We need to track the read position
    
    // Read from slot corresponding to last_sequence + 1
    uint64_t next_seq = reader->last_sequence + 1;
    int slot_idx = next_seq % BUFFER_SLOTS;
    size_t slot_offset = slot_idx * SLOT_SIZE;
    
    // Copy frame data
    memcpy(frame, (uint8_t*)reader->shm_ptr + slot_offset, SLOT_SIZE);
    
    // Validate magic number
    if (frame->header.magic != MAGIC_NUMBER) {
        fprintf(stderr, "Invalid magic number: 0x%08X (expected 0x%08X)\n",
                frame->header.magic, MAGIC_NUMBER);
        return false;
    }
    
    // Check for dropped frames
    if (reader->frames_read > 0) {
        uint64_t expected_seq = reader->last_sequence + 1;
        if (frame->header.frame_sequence > expected_seq) {
            uint64_t dropped = frame->header.frame_sequence - expected_seq;
            reader->frames_dropped += dropped;
            fprintf(stderr, "Warning: Dropped %lu frame(s)\n", dropped);
        }
    }
    
    reader->last_sequence = frame->header.frame_sequence;
    reader->frames_read++;
    
    return true;
}

uint64_t shm_reader_get_frames_read(const ShmReader* reader) {
    return reader ? reader->frames_read : 0;
}

uint64_t shm_reader_get_frames_dropped(const ShmReader* reader) {
    return reader ? reader->frames_dropped : 0;
}

void shm_reader_destroy(ShmReader* reader) {
    if (!reader) {
        return;
    }
    
    printf("ShmReader: Cleanup (read=%lu, dropped=%lu)\n",
           reader->frames_read, reader->frames_dropped);
    
    if (reader->sem_write != SEM_FAILED) {
        sem_close(reader->sem_write);
    }
    
    if (reader->shm_ptr != MAP_FAILED) {
        munmap(reader->shm_ptr, reader->shm_size);
    }
    
    if (reader->shm_fd != -1) {
        close(reader->shm_fd);
    }
    
    free(reader);
}
