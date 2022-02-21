IMAGE_NAME := mamercad/ambientweather-exporter

ifeq ($(IMAGE_TAG),)
IMAGE_TAG := latest
endif

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
		docker.io/$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: run-influx
run-influx: build
	docker run -it -p 10102:10102/tcp \
		-e AMBI_APP_KEY=$(AMBI_APP_KEY) \
		-e AMBI_API_KEY=$(AMBI_API_KEY) \
		-e INFLUX_ENABLE=True \
		-e INFLUX_HOST=$(INFLUX_HOST) \
		docker.io/$(IMAGE_NAME):$(IMAGE_TAG)

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

.PHONY: helm-local
helm-local:
	helm install my-ambientweather-exporter \
	  --namespace ambientweather --create-namespace \
		--set deployment.tag="$(IMAGE_TAG)" \
	  --set service.type="LoadBalancer" \
	  --set secret.ambi_app_key="$(AMBI_APP_KEY)" \
	  --set secret.ambi_api_key="$(AMBI_API_KEY)" \
		--set influx.enable=false \
		./charts/ambientweather-exporter
