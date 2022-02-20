IMAGE_NAME := mamercad/ambientweather-exporter
IMAGE_TAG := latest

.PHONY: build
build:
	docker build -t docker.io/$(IMAGE_NAME):$(IMAGE_TAG) .
	docker build -t ghcr.io/$(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: push
push: build
	docker push docker.io/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push ghcr.io/$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: run
run: build
	docker run -it -p 10102:10102/tcp \
		-e AMBI_APP_KEY=$(AMBI_APP_KEY) \
		-e AMBI_API_KEY=$(AMBI_API_KEY) \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: run-influx
run-influx: build
	docker run -it -p 10102:10102/tcp \
		-e AMBI_APP_KEY=$(AMBI_APP_KEY) \
		-e AMBI_API_KEY=$(AMBI_API_KEY) \
		-e INFLUX_ENABLE=True \
		-e INFLUX_HOST=$(INFLUX_HOST) \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: compose-up
compose-up: build
	docker compose up -d

.PHONY: compose-down
compose-down:
	docker compose down

.PHONY: install
install:
	cp ambientweather-exporter.py /usr/local/bin/
	cp ambientweather-exporter.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable ambientweather-exporter
	systemctl start ambientweather-exporter
