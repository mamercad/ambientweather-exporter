FROM python:alpine3.15

RUN  mkdir /app
COPY ./requirements.txt /app/requirements.txt
RUN  pip3 install -r /app/requirements.txt
COPY ambientweather-exporter.py /app

ENTRYPOINT [ "python3" ]
CMD [ "/app/ambientweather-exporter.py" ]
