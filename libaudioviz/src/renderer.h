#pragma once
#include <vector>
#include <SDL2/SDL.h>

class Renderer {
public:
    Renderer(int width, int height);
    ~Renderer();

    // Opens the GUI window
    void initialize_window();

    // Main render loop step
    void render_frame(float* data, size_t size);
    
    // Set visual mode
    void set_mode(int mode);

    enum VisualMode {
        BARS = 0,
        CIRCLE = 1
    };

private:
    void draw_bars(float* data, size_t size);
    void draw_circle(float* data, size_t size);

    int width_;
    int height_;
    float center_x_;
    int current_mode_ = 0; // Default to BARS

    SDL_Window* window_;
    SDL_Renderer* renderer_;
};