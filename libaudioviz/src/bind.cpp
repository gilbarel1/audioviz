#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <complex>
#include <iostream>

#include "renderer.h"

namespace py = pybind11;

// Wrapper function to handle NumPy buffer conversion safely
void render_frame_wrapper(Renderer& self, py::array_t<float> input_array) {
    // Request access to the numpy buffer (efficient, no copy if format matches)
    py::buffer_info buf = input_array.request();

    if (buf.ndim != 1) {
        throw std::runtime_error("Number of dimensions must be 1 (Audio Buffer)");
    }

    // Cast the raw data pointer to C++ complex float pointer
    auto* ptr = static_cast<float*>(buf.ptr);
    size_t size = buf.shape[0];

    // Pass the raw pointer and size to your C++ logic
    self.render_frame(ptr, size);
}

PYBIND11_MODULE(_libaudioviz, m) {
    m.doc() = "C++ Audioviz Renderer Extension";

    py::class_<Renderer>(m, "Renderer")
        .def(py::init<int, int>(), py::arg("width"), py::arg("height"))
        .def("initialize_window", &Renderer::initialize_window, "Open the visualization window")
        .def("render_frame", &render_frame_wrapper, "Draw the frame based on current data");
}