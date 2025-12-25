cmake_minimum_required(VERSION 3.28)

project(audioviz_renderer LANGUAGES C)

# Set C standard
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Enable strict warnings
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Werror")

# Add executable
add_executable(audioviz_renderer
    src/main.c
)

# Set output directory
set_target_properties(audioviz_renderer PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../build"
)
