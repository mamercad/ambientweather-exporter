FROM ubuntu:18.04

RUN apt update
RUN apt-get -y install python3 python3-pip

RUN  mkdir /app
COPY ./requirements.txt /app/requirements.txt
RUN  pip3 install -r /app/requirements.txt
COPY ambientweather-exporter.py /app

ENTRYPOINT [ "python3" ]
CMD [ "/app/ambientweather-exporter.py" ]
