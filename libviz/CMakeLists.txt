cmake_minimum_required(VERSION 3.15)
project(audioviz_renderer C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Compiler flags
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Source files
set(SOURCES
    src/main.c
    src/shm_reader.c
    src/renderer.c
    src/visualizers/bars.c
)

# Executable
add_executable(audioviz_renderer ${SOURCES})

# Include directories
target_include_directories(audioviz_renderer PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/bindings
)

# Link libraries (POSIX threads and real-time)
target_link_libraries(audioviz_renderer PRIVATE
    pthread
    rt
    m
)

# Optional: SDL3 and OpenGL (commented out for stub build)
# find_package(SDL3 REQUIRED)
# find_package(OpenGL REQUIRED)
# target_link_libraries(audioviz_renderer PRIVATE SDL3::SDL3 ${OPENGL_LIBRARIES})

# Install target
install(TARGETS audioviz_renderer DESTINATION bin)

# Print configuration summary
message(STATUS "")
message(STATUS "AudioViz Renderer Configuration:")
message(STATUS "  C Compiler: ${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Install Prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "")
