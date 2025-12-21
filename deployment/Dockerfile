FROM ubuntu:latest

# Set environment variables to avoid interactive prompts during installations
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash-completion direnv \
    gcc g++ make cmake ninja-build git \
    python3 python3-dev python3-pip python3-venv \
    libsndfile1 libsndfile1-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python3 as python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Create and activate a virtual environment
RUN python3 -m venv /venv

# Upgrade pip and install necessary Python packages
RUN /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install pytest soundfile scipy numpy

# Set the virtual environment as the default Python environment
ENV PATH="/venv/bin:$PATH"

# Configure shell
RUN echo 'source /venv/bin/activate' >> /root/.bashrc && \
    echo 'eval "$(direnv hook bash)"' >> /root/.bashrc && \
    echo 'cd /workspace' >> /root/.bashrc

RUN echo "🎵 AudioViz Development Environment Ready! 🎵"
