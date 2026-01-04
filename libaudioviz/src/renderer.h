#pragma once
#include <vector>
#include <tuple>
#include <string>
#include <SDL2/SDL.h>

/**
 * Low-level renderer that provides primitive drawing operations.
 * This class knows nothing about visualization modes - it only draws
 * what it's told to draw by the Python layer.
 */
class Renderer {
public:
    Renderer(int width, int height);
    ~Renderer();

    // Window management
    void initialize_window();
    int get_width() const { return width_; }
    int get_height() const { return height_; }

    // Frame operations
    void clear(uint8_t r, uint8_t g, uint8_t b, uint8_t a);
    void present();

    // Primitive drawing - batched for efficiency
    void draw_rectangles(const std::vector<std::tuple<int, int, int, int>>& rects,
                         uint8_t r, uint8_t g, uint8_t b, uint8_t a);
    
    void draw_lines(const std::vector<std::tuple<int, int, int, int>>& lines,
                    uint8_t r, uint8_t g, uint8_t b, uint8_t a);

    // Event handling
    std::vector<std::tuple<std::string, int, int>> poll_events();
    bool should_quit() const { return should_quit_; }

private:
    int width_;
    int height_;
    bool should_quit_ = false;

    SDL_Window* window_ = nullptr;
    SDL_Renderer* renderer_ = nullptr;
};