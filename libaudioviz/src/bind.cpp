#include <pybind11/pybind11.h>
#include "audioviz.h"

namespace py = pybind11;

PYBIND11_MODULE(_libaudioviz, m) {
    
    m.doc() = "Audio visualization library - C++ implementation";
// placeholder- not real implementation
    m.def("get_version", &audioviz::get_version,
          "Get the library version");
}
