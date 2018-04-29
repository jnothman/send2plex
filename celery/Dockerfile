FROM ubuntu:xenial
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev
RUN apt-get install -y ffmpeg
COPY . /celery
WORKDIR /celery
RUN pip install -r requirements.txt
CMD [ "celery", "-A", "tasks", "worker", "--loglevel=info" ]