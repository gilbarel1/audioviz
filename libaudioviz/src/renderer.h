#pragma once
#include <vector>
#include <complex>

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
};