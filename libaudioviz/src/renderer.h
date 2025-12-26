#pragma once
#include <vector>
#include <complex>

class Renderer {
public:
    Renderer(int width, int height);
    ~Renderer();

    // Opens the GUI window (if your C library handles this)
    void initialize_window();

    // Receives data from Python (called by the bind )
    void update_data(std::complex<float>* data, size_t size);

    // Main render loop step
    void render_frame();

private:

    int width_;
    int height_;
};