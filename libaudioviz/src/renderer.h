#pragma once
#include <vector>
#include <tuple>
#include <string>
#include <unordered_map>
#include <SDL2/SDL.h>
#include <SDL2/SDL_ttf.h>

/**
 * Low-level renderer that provides primitive drawing operations.
 * This class knows nothing about visualization modes - it only draws
 * what it's told to draw by the Python layer.
 */
class Renderer {
public:
    struct Rect {
        int x, y, w, h;
    };

    struct Line {
        int x1, y1, x2, y2;
    };

    Renderer(int width, int height);
    ~Renderer();

    // Window management
    void initialize_window(const std::string& font_path);
    int get_width() const { return width_; }
    int get_height() const { return height_; }

    // Frame operations
    void clear(uint8_t r, uint8_t g, uint8_t b, uint8_t a);
    void present();

    // Primitive drawing - batched for efficiency
    void draw_rectangles(const std::vector<Rect>& rects,
                         uint8_t r, uint8_t g, uint8_t b, uint8_t a);
    
    void draw_lines(const std::vector<Line>& lines,
                    uint8_t r, uint8_t g, uint8_t b, uint8_t a);
    
    // Text rendering
    void draw_text(const std::string& text, int x, int y,
                   uint8_t r, uint8_t g, uint8_t b, uint8_t a);

    // Event handling - returns list of (event_type, params) tuples
    std::vector<std::tuple<std::string, std::vector<int>>> poll_events();
    bool should_quit() const { return should_quit_; }

private:
    int width_;
    int height_;
    bool should_quit_ = false;

    SDL_Window* window_ = nullptr;
    SDL_Renderer* renderer_ = nullptr;
    TTF_Font* font_ = nullptr;
    
    // Cache for text textures (key: text string, value: source texture)
    std::unordered_map<std::string, SDL_Texture*> text_cache_;
};