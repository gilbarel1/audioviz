# audioviz

This project is a basic cross-language system for visualizing music, inspired by classic audio visualizers.  
The goal is to process audio in **Python** and render visuals in **C**, with a clean separation between the two parts.

## Overview

- Python loads an audio file, splits it into buffers, and performs Fourier transforms.
- The processed frequency data is passed to a C component.
- The C component is responsible for drawing the visual effects.

## Features

- Audio handling and FFT processing in Python.
- Graphics rendering in C.
- Clear separation of concerns between languages.
- Simple architecture suitable as a template for future expansion.

## Repository Structure (High-Level)
To be continued...


