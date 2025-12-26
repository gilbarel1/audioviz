#include "renderer.h"
#include <iostream>


// for now, i implemented a dummy class doing basicly nothing but printing bullshit. 
//TODO add real impl...
Renderer::Renderer(int width, int height) : width_(width), height_(height) {
    std::cout << "Renderer created (" << width << "x" << height << ")" << std::endl;
}

Renderer::~Renderer() {
    std::cout << "Renderer destroyed" << std::endl;
}

void Renderer::initialize_window() {
    std::cout << "Window initialized" << std::endl;
}


void Renderer::render_frame(std::complex<float>* data, size_t size) {
    std::cout << "Frame rendered" << std::endl;
    if (size > 0) {
        std::cout << "Data[0]: " << data[0] << " | Size: " << size << std::endl;
    } 
}