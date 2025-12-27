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

    // draw 
    // We determine the width of each bar based on the window width and number of frequency bins
    if (size > 0) {

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

    // present to screen- update 
    SDL_RenderPresent(renderer_);
}


