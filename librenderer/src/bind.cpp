#include <pybind11/pybind11.h>

int test_init() {
    return 0;
}

PYBIND11_MODULE(_librenderer, m) {
    m.doc() = "pybind11 example plugin"; // optional module docstring
    m.def("test_init", &test_init, "A function that returns 0 to verify binding works");
}
