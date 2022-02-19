.PHONY: build
build:
	docker build -t ambientweather-exporter:latest .

.PHONY: compose
compose:
	docker-compose up

.PHONY: install
install:
	cp ambientweather-exporter.py /usr/local/bin/
	cp ambientweather-exporter.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable ambientweather-exporter
	systemctl start ambientweather-exporter
