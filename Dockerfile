FROM ubuntu:20.04
RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-pip && \
    apt-get install -y ffmpeg && apt-get install libopus0

WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
CMD python3 bot.py
