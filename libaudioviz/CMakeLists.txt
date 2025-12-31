cmake_minimum_required(VERSION 3.15)
project(libaudioviz LANGUAGES CXX)

# Find Pybind11 (It will be installed automatically by pyproject.toml)
find_package(pybind11 CONFIG REQUIRED)

# Fetch SDL2 via FetchContent for portability
include(FetchContent)
FetchContent_Declare(
    SDL2
    GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
    GIT_TAG release-2.30.0  # Pin to a stable version
    GIT_SHALLOW TRUE
)
set(SDL_SHARED OFF CACHE BOOL "Build SDL2 as a shared library" FORCE)
set(SDL_STATIC ON CACHE BOOL "Build SDL2 as a static library" FORCE)
set(SDL_TEST OFF CACHE BOOL "Build SDL2 test" FORCE)
FetchContent_MakeAvailable(SDL2)

# Define the source files
set(SOURCES
    src/bind.cpp
    src/renderer.cpp
)

# Create the python module
# "_libaudioviz" is the name Python will import
pybind11_add_module(_libaudioviz MODULE ${SOURCES})

# Link against SDL2-static (created by FetchContent)
if(TARGET SDL2::SDL2-static)
    target_link_libraries(_libaudioviz PRIVATE SDL2::SDL2-static)
elseif(TARGET SDL2-static)
    target_link_libraries(_libaudioviz PRIVATE SDL2-static)
else()
     # Fallback or shared
    target_link_libraries(_libaudioviz PRIVATE SDL2::SDL2)
endif()

# On Windows we need to link these system libraries when using static SDL2
if(WIN32)
    target_link_libraries(_libaudioviz PRIVATE user32 gdi32 winmm imm32 ole32 oleaut32 version uuid advapi32 setupapi shell32)
endif()

# Set standard C++ version
target_compile_features(_libaudioviz PRIVATE cxx_std_17)


# INSTALL RULE: Put the compiled extension into the python package folder
install(TARGETS _libaudioviz DESTINATION libaudioviz)