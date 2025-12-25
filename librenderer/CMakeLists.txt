cmake_minimum_required(VERSION 3.15)
project(_librenderer LANGUAGES CXX)

find_package(pybind11 REQUIRED)

pybind11_add_module(_librenderer src/bind.cpp)

install(TARGETS _librenderer DESTINATION librenderer)
