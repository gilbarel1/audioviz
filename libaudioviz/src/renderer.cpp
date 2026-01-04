#include "renderer.h"
#include <iostream>
#include <algorithm>

Renderer::Renderer(int width, int height) : width_(width), height_(height) {
    std::cout << "Renderer created (" << width << "x" << height << ")" << std::endl;
}

Renderer::~Renderer() {
    if (renderer_) {
        SDL_DestroyRenderer(renderer_);
    }
    if (window_) {
        SDL_DestroyWindow(window_);
    }
    SDL_Quit();
    std::cout << "Renderer destroyed" << std::endl;
}

void Renderer::initialize_window() {
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        throw std::runtime_error("SDL could not initialize! SDL_Error: " + std::string(SDL_GetError()));
    }

    window_ = SDL_CreateWindow(
        "AudioViz Renderer",
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        width_,
        height_,
        SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
    );

    if (!window_) {
        SDL_Quit();
        throw std::runtime_error("Window could not be created! SDL_Error: " + std::string(SDL_GetError()));
    }

    renderer_ = SDL_CreateRenderer(window_, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);

    if (!renderer_) {
        SDL_DestroyWindow(window_);
        SDL_Quit();
        window_ = nullptr;
        throw std::runtime_error("Renderer could not be created! SDL_Error: " + std::string(SDL_GetError()));
    }

    std::cout << "Window initialized" << std::endl;
}

void Renderer::clear(uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    SDL_SetRenderDrawColor(renderer_, r, g, b, a);
    SDL_RenderClear(renderer_);
}

void Renderer::present() {
    SDL_RenderPresent(renderer_);
}

void Renderer::draw_rectangles(const std::vector<std::tuple<int, int, int, int>>& rects,
                                uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    SDL_SetRenderDrawColor(renderer_, r, g, b, a);
    
    for (const auto& rect : rects) {
        SDL_Rect sdl_rect = {
            std::get<0>(rect),  // x
            std::get<1>(rect),  // y
            std::get<2>(rect),  // width
            std::get<3>(rect)   // height
        };
        SDL_RenderFillRect(renderer_, &sdl_rect);
    }
}

void Renderer::draw_lines(const std::vector<std::tuple<int, int, int, int>>& lines,
                          uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    SDL_SetRenderDrawColor(renderer_, r, g, b, a);
    
    for (const auto& line : lines) {
        SDL_RenderDrawLine(
            renderer_,
            std::get<0>(line),  // x1
            std::get<1>(line),  // y1
            std::get<2>(line),  // x2
            std::get<3>(line)   // y2
        );
    }
}

std::vector<std::tuple<std::string, int, int>> Renderer::poll_events() {
    std::vector<std::tuple<std::string, int, int>> events;
    SDL_Event e;
    
    while (SDL_PollEvent(&e) != 0) {
        if (e.type == SDL_QUIT) {
            should_quit_ = true;
            events.push_back({"quit", 0, 0});
        }
        else if (e.type == SDL_KEYDOWN) {
            events.push_back({"keydown", e.key.keysym.sym, 0});
        }
        else if (e.type == SDL_KEYUP) {
            events.push_back({"keyup", e.key.keysym.sym, 0});
        }
        else if (e.type == SDL_WINDOWEVENT) {
            if (e.window.event == SDL_WINDOWEVENT_RESIZED) {
                width_ = e.window.data1;
                height_ = e.window.data2;
                events.push_back({"resize", width_, height_});
            }
        }
    }
    
    return events;
}
