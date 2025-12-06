/**
 * Shared Memory Reader
 * 
 * Consumes FFT frames from shared memory circular buffer.
 */

#ifndef SHM_READER_H
#define SHM_READER_H

#include <stdbool.h>
#include "../bindings/shm_protocol.h"

typedef struct ShmReader ShmReader;

/**
 * Initialize shared memory reader.
 * 
 * @param shm_name Shared memory segment name
 * @param create If true, create segment; if false, attach to existing
 * @return Pointer to reader instance, or NULL on failure
 */
ShmReader* shm_reader_init(const char* shm_name, bool create);

/**
 * Read next available frame (blocking).
 * 
 * @param reader Reader instance
 * @param frame Output buffer for frame data
 * @param timeout_ms Timeout in milliseconds (0 = no timeout)
 * @return true if frame read successfully, false on timeout/error
 */
bool shm_reader_read_frame(ShmReader* reader, Frame* frame, int timeout_ms);

/**
 * Get statistics.
 */
uint64_t shm_reader_get_frames_read(const ShmReader* reader);
uint64_t shm_reader_get_frames_dropped(const ShmReader* reader);

/**
 * Cleanup and destroy reader.
 */
void shm_reader_destroy(ShmReader* reader);

#endif // SHM_READER_H
