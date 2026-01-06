#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <tuple>
#include <vector>
#include <string>

#include "renderer.h"

namespace py = pybind11;

PYBIND11_MODULE(_libaudioviz, m) {
    m.doc() = "C++ Audioviz Renderer Extension - Primitive Drawing Layer";

    py::class_<Renderer::Rect>(m, "Rect")
        .def(py::init<int, int, int, int>(), py::arg("x"), py::arg("y"), py::arg("w"), py::arg("h"))
        .def_readwrite("x", &Renderer::Rect::x)
        .def_readwrite("y", &Renderer::Rect::y)
        .def_readwrite("w", &Renderer::Rect::w)
        .def_readwrite("h", &Renderer::Rect::h);

    py::class_<Renderer::Line>(m, "Line")
        .def(py::init<int, int, int, int>(), py::arg("x1"), py::arg("y1"), py::arg("x2"), py::arg("y2"))
        .def_readwrite("x1", &Renderer::Line::x1)
        .def_readwrite("y1", &Renderer::Line::y1)
        .def_readwrite("x2", &Renderer::Line::x2)
        .def_readwrite("y2", &Renderer::Line::y2);

    py::class_<Renderer>(m, "Renderer")
        .def(py::init<int, int>(), py::arg("width"), py::arg("height"))
        
        // Window management
        .def("initialize_window", &Renderer::initialize_window, "Open the visualization window")
        .def("get_width", &Renderer::get_width, "Get current window width")
        .def("get_height", &Renderer::get_height, "Get current window height")
        
        // Frame operations
        .def("clear", &Renderer::clear, 
             py::arg("r"), py::arg("g"), py::arg("b"), py::arg("a"),
             "Clear screen with specified RGBA color")
        .def("present", &Renderer::present, "Present the rendered frame to screen")
        
        // Primitive drawing
        .def("draw_rectangles", &Renderer::draw_rectangles,
             py::arg("rects"), py::arg("r"), py::arg("g"), py::arg("b"), py::arg("a"),
             "Draw batch of filled rectangles. Each rect is (x, y, w, h)")
        .def("draw_lines", &Renderer::draw_lines,
             py::arg("lines"), py::arg("r"), py::arg("g"), py::arg("b"), py::arg("a"),
             "Draw batch of lines. Each line is (x1, y1, x2, y2)")
        
        // Event handling
        .def("poll_events", &Renderer::poll_events,
             "Poll SDL events. Returns list of (event_type, data1, data2) tuples")
        .def("should_quit", &Renderer::should_quit, "Check if quit was requested");
}