#include "renderer.h"
#include <iostream>
#include <algorithm>
#include <cmath>


Renderer::Renderer(int width, int height) : width_(width), height_(height), window_(nullptr), renderer_(nullptr) {
    std::cout << "Renderer created (" << width << "x" << height << ")" << std::endl;
    center_x_ = width_ / 2.0f; //calculated once 
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
        SDL_WINDOW_SHOWN
    );

    if (!window_) { 
        SDL_Quit(); // clean up 
        throw std::runtime_error("Window could not be created! SDL_Error: " + std::string(SDL_GetError()));
    }

    renderer_ = SDL_CreateRenderer(window_, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    
    if (!renderer_) {
        SDL_DestroyWindow(window_);
        SDL_Quit(); // clean up 
        window_ = nullptr;
        throw std::runtime_error("Renderer could not be created! SDL_Error: " + std::string(SDL_GetError()));
    }

    // this print is for debug for now, later i will remove it 
    std::cout << "Window initialized" << std::endl;
}

void Renderer::set_mode(int mode) {
    if (mode >= 0 && mode <= VisualizationState::modes.size()) { // Len of visual modes
        current_mode_ = mode;
    }
}

//take care of all events in queue-> clean the screen-> present one image
void Renderer::render_frame(float* data, size_t size) {
    
    // take care of sdl events 
    SDL_Event e;
    while (SDL_PollEvent(&e) != 0) {
        if (e.type == SDL_QUIT) {
            // for now, for every event, just continue the loop
            // TODO- next step is signal python for sync and take care for real events.
            //TODO- calculate center again if window resized
            
        }
    }

    // clean the screen
    SDL_SetRenderDrawColor(renderer_, 0, 0, 0, 255);
    SDL_RenderClear(renderer_);

    if (size > 0) {
        if (current_mode_ == BARS) {
            draw_bars(data, size);
        } else if (current_mode_ == CIRCLE) {
            draw_circle(data, size);
        }
    }

    // present to screen- update 
    SDL_RenderPresent(renderer_);
}

void Renderer::draw_bars(float* data, size_t size) {
    //bar width 
    float bar_width = static_cast<float>(width_) / size;
    if (bar_width < 1.0f) bar_width = 1.0f;

    SDL_SetRenderDrawColor(renderer_, 0, 255, 0, 255); // for now, we will present everything in green
    //TODO- idea- maybe change colors? let user pick color(s)? make it rainbow? idk

    for (size_t i = 0; i < size; ++i) {
        
        // scaling and normalization
        // linear visualization.
        float magnitude = data[i];
        float bar_height = std::min(magnitude * 5000.0f, static_cast<float>(height_));

        //trying to draw a mirroring visualization from center

        //draw right
        SDL_Rect rightRect = {
            static_cast<int>(center_x_ + (i * bar_width)),           // x
            static_cast<int>(height_ - bar_height),    // y (from bottom)
            static_cast<int>(std::ceil(bar_width)),    // width
            static_cast<int>(bar_height)               // height
        };

        SDL_RenderFillRect(renderer_, &rightRect);

        //draw left
        SDL_Rect leftRect = {
            static_cast<int>(center_x_ - ((i + 1) * bar_width)), 
            static_cast<int>(height_ - bar_height),
            static_cast<int>(std::ceil(bar_width)),
            static_cast<int>(bar_height)
        };
        SDL_RenderFillRect(renderer_, &leftRect);
    }
}

void Renderer::draw_circle(float* data, size_t size) {
    int center_y = height_ / 2;
    float max_radius = std::min(width_, height_) / 2.0f;
    float base_radius = max_radius * 0.2f; // Inner circle
    
    SDL_SetRenderDrawColor(renderer_, 0, 255, 255, 255); // Cyan for circle mode

    float angle_step = 2.0f * M_PI / size;

    for (size_t i = 0; i < size; ++i) {
        float magnitude = data[i];
        float line_len = std::min(magnitude * 3000.0f, max_radius - base_radius);
        
        float angle = i * angle_step;
        
        // Start point (on base circle)
        int x1 = static_cast<int>(center_x_ + std::cos(angle) * base_radius);
        int y1 = static_cast<int>(center_y + std::sin(angle) * base_radius);
        
        // End point
        int x2 = static_cast<int>(center_x_ + std::cos(angle) * (base_radius + line_len));
        int y2 = static_cast<int>(center_y + std::sin(angle) * (base_radius + line_len));
        
        SDL_RenderDrawLine(renderer_, x1, y1, x2, y2);
        
        // Mirror for full circle if data is only half spectrum? 
        
        float angle_mirror = -angle;
         // Start point (mirror)
        int x1m = static_cast<int>(center_x_ + std::cos(angle_mirror) * base_radius);
        int y1m = static_cast<int>(center_y + std::sin(angle_mirror) * base_radius);
        
        // End point (mirror)
        int x2m = static_cast<int>(center_x_ + std::cos(angle_mirror) * (base_radius + line_len));
        int y2m = static_cast<int>(center_y + std::sin(angle_mirror) * (base_radius + line_len));
         SDL_RenderDrawLine(renderer_, x1m, y1m, x2m, y2m);
    }
}


