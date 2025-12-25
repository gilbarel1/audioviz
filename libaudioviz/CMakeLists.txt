cmake_minimum_required(VERSION 3.28)
project(libaudioviz LANGUAGES CXX)

# Enable pybind11 from scikit-build-core
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 REQUIRED)

# Optionally enable coverage instrumentation
option(ENABLE_COVERAGE "Enable coverage instrumentation" OFF)
if(ENABLE_COVERAGE)
    message(STATUS "Building with coverage support")
endif()

add_library(_libaudioviz MODULE
    src/audioviz.cpp
    src/bind.cpp
)

target_compile_features(_libaudioviz PRIVATE cxx_std_17)

# Warnings and treat warnings as errors
if (MSVC)
    target_compile_options(_libaudioviz PRIVATE /W4 /WX)
else()
    target_compile_options(_libaudioviz PRIVATE -Wall -Wextra -Werror)
endif()

# Coverage flags
if(ENABLE_COVERAGE)
    target_compile_options(_libaudioviz PRIVATE --coverage -fprofile-arcs -ftest-coverage -O0)
    target_link_options(_libaudioviz PRIVATE --coverage)
    target_link_libraries(_libaudioviz PRIVATE gcov)
endif()

target_link_libraries(_libaudioviz PRIVATE pybind11::module)
target_include_directories(_libaudioviz PRIVATE ${pybind11_INCLUDE_DIRS})

pybind11_extension(_libaudioviz)

set_target_properties(_libaudioviz PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)
