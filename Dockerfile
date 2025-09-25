FROM ubuntu:22.04

# Install Python 3.11, pip, ffmpeg, and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r /tmp/requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 80

# Run app
CMD ["python3", "main.py"]
