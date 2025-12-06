/**
 * Graphics Renderer Interface
 * 
 * Abstract interface for visualization algorithms.
 */

#ifndef RENDERER_H
#define RENDERER_H

#include <stdbool.h>
#include <stdint.h>

typedef struct Renderer Renderer;

/**
 * Renderer configuration.
 */
typedef struct {
    int window_width;
    int window_height;
    const char* title;
    bool vsync;
    int target_fps;
} RendererConfig;

/**
 * Initialize renderer (SDL3 + OpenGL).
 * 
 * @param config Configuration parameters
 * @return Renderer instance, or NULL on failure
 */
Renderer* renderer_init(const RendererConfig* config);

/**
 * Render a frame with FFT magnitude data.
 * 
 * @param renderer Renderer instance
 * @param magnitude FFT magnitude bins (normalized 0-1)
 * @param bin_count Number of bins
 * @return true if rendered successfully
 */
bool renderer_render_frame(Renderer* renderer, const float* magnitude, int bin_count);

/**
 * Process window events.
 * 
 * @param renderer Renderer instance
 * @return true if should continue, false if quit requested
 */
bool renderer_process_events(Renderer* renderer);

/**
 * Get renderer statistics.
 */
uint64_t renderer_get_frame_count(const Renderer* renderer);
double renderer_get_average_fps(const Renderer* renderer);

/**
 * Cleanup and destroy renderer.
 */
void renderer_destroy(Renderer* renderer);

#endif // RENDERER_H
