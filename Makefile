.PHONY: build
build:
	docker build -t ambientweather-exporter:latest .

.PHONY: run
run:
	docker run --rm -p 10102:10102/tcp ambientweather-exporter:latest

.PHONY: install
install:
	cp ambientweather-exporter.py /usr/local/bin/
	cp ambientweather-exporter.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable ambientweather-exporter
	systemctl start ambientweather-exporter
