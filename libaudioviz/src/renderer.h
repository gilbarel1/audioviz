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

private:

    int width_;
    int height_;
    float center_x_;

    SDL_Window* window_;
    SDL_Renderer* renderer_;
};