FROM python:3.11

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
#ENV RAILS_SERVE_STATIC_FILES="true"

# create the app directory - and switch to it
RUN mkdir -p /app
WORKDIR /app

# RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-pip
# RUN pip install --upgrade pip

# install dependencies
RUN apt-get -y update && apt-get install -y ffmpeg

# install dependencies
COPY requirements.txt /tmp/requirements.txt
# RUN pip install -r requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/


# copy project
COPY . /app/
# expose port 80
EXPOSE 80
CMD python3 main.py
# CMD ["gunicorn", "--bind", ":8000", "--workers", "1", "personal_site.wsgi:application"]
#CMD python3 main.py
