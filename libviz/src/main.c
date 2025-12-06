/**
 * Main Entry Point for AudioViz Renderer
 * 
 * Coordinates shared memory reading and graphics rendering.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <signal.h>
#include <unistd.h>
#include "shm_reader.h"
#include "renderer.h"
#include "../bindings/shm_protocol.h"

static volatile bool g_running = true;

static void signal_handler(int sig) {
    printf("\nReceived signal %d, shutting down...\n", sig);
    g_running = false;
}

int main(int argc, char* argv[]) {
    printf("AudioViz Renderer v0.1.0\n");
    printf("========================\n\n");
    
    // Setup signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // Initialize components
    printf("Initializing shared memory reader...\n");
    ShmReader* reader = shm_reader_init(SHM_NAME, false);  // Attach to existing
    if (!reader) {
        fprintf(stderr, "Failed to initialize shared memory reader\n");
        fprintf(stderr, "Make sure the Python audio processor is running first.\n");
        return 1;
    }
    
    printf("Initializing renderer...\n");
    RendererConfig config = {
        .window_width = 1280,
        .window_height = 720,
        .title = "AudioViz - Music Visualizer",
        .vsync = true,
        .target_fps = 60
    };
    
    Renderer* renderer = renderer_init(&config);
    if (!renderer) {
        fprintf(stderr, "Failed to initialize renderer\n");
        shm_reader_destroy(reader);
        return 1;
    }
    
    printf("\nRenderer started. Press Ctrl+C to exit.\n");
    printf("Waiting for audio frames...\n\n");
    
    // Main event loop
    Frame frame;
    uint64_t last_print = 0;
    
    while (g_running) {
        // Process window events
        if (!renderer_process_events(renderer)) {
            printf("Window closed by user\n");
            break;
        }
        
        // Read frame from shared memory (100ms timeout)
        if (shm_reader_read_frame(reader, &frame, 100)) {
            // Render frame
            bool success = renderer_render_frame(
                renderer, 
                frame.magnitude, 
                frame.header.bin_count
            );
            
            if (!success) {
                fprintf(stderr, "Rendering failed\n");
                break;
            }
            
            // Print statistics every 100 frames
            uint64_t frames_read = shm_reader_get_frames_read(reader);
            if (frames_read - last_print >= 100) {
                printf("Stats: read=%lu, dropped=%lu, rendered=%lu, fps=%.1f\n",
                       frames_read,
                       shm_reader_get_frames_dropped(reader),
                       renderer_get_frame_count(renderer),
                       renderer_get_average_fps(renderer));
                last_print = frames_read;
            }
        }
    }
    
    // Cleanup
    printf("\nShutting down...\n");
    renderer_destroy(renderer);
    shm_reader_destroy(reader);
    
    printf("Goodbye!\n");
    return 0;
}
