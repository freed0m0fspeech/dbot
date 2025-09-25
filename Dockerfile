FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3.11-dev python3-pip ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

COPY . /app/
EXPOSE 80
CMD ["python3", "main.py"]
