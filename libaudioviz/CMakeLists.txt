cmake_minimum_required(VERSION 3.15)
project(libaudioviz LANGUAGES CXX)

# Find Pybind11 (It will be installed automatically by pyproject.toml)
find_package(pybind11 CONFIG REQUIRED)

# Define the source files
set(SOURCES
    src/bind.cpp
    src/renderer.cpp
)

# Create the python module
# "_libaudioviz" is the name Python will import
pybind11_add_module(_libaudioviz MODULE ${SOURCES})

# Link libraries (Add your C-library here later)
# target_link_libraries(_libaudioviz PRIVATE your_c_lib)

# Set standard C++ version
target_compile_features(_libaudioviz PRIVATE cxx_std_17)


# INSTALL RULE: Put the compiled extension into the python package folder
install(TARGETS _libaudioviz DESTINATION libaudioviz)