cmake_minimum_required(VERSION 3.15)
project(libaudioviz LANGUAGES CXX)

# Find Pybind11 (It will be installed automatically by pyproject.toml)
find_package(pybind11 CONFIG REQUIRED)

# Find SDL2
find_package(SDL2 REQUIRED)
include_directories(${SDL2_INCLUDE_DIRS})

# Find SDL2_ttf
find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2_TTF REQUIRED SDL2_ttf)
include_directories(${SDL2_TTF_INCLUDE_DIRS})

# Define the source files
set(SOURCES
    src/bind.cpp
    src/renderer.cpp
)

# Create the python module
# "_libaudioviz" is the name Python will import
pybind11_add_module(_libaudioviz MODULE ${SOURCES})

# Link against SDL2 and SDL2_ttf
target_link_libraries(_libaudioviz PRIVATE SDL2::SDL2 ${SDL2_TTF_LIBRARIES})

# On Windows we need to link these system libraries when using static SDL2
if(WIN32)
    target_link_libraries(_libaudioviz PRIVATE user32 gdi32 winmm imm32 ole32 oleaut32 version uuid advapi32 setupapi shell32)
endif()

# Set standard C++ version
target_compile_features(_libaudioviz PRIVATE cxx_std_17)


# INSTALL RULE: Put the compiled extension into the python package folder
install(TARGETS _libaudioviz DESTINATION libaudioviz)