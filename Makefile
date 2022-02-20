.PHONY: build
build:
	docker build -t docker.io/mamercad/ambientweather-exporter:latest .
	docker build -t ghcr.io/mamercad/ambientweather-exporter:latest .

.PHONY: run
run:
	docker run -it -p 10102:10102/tcp \
		-e AMBI_APP_KEY=$(AMBI_APP_KEY) \
		-e AMBI_API_KEY=$(AMBI_API_KEY) \
		-e INFLUX_ENABLE=true \
		-e INFLUX_HOST=192.168.1.105 \
		-e INFLUX_INTERVAL=0 \
		mamercad/ambientweather-exporter:latest

.PHONY: push
push: build
	docker push docker.io/mamercad/ambientweather-exporter:latest
	docker push ghcr.io/mamercad/ambientweather-exporter:latest

.PHONY: compose
compose: build
	docker compose up

.PHONY: install
install:
	cp ambientweather-exporter.py /usr/local/bin/
	cp ambientweather-exporter.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable ambientweather-exporter
	systemctl start ambientweather-exporter
