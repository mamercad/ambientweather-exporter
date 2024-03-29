#!/usr/bin/env python3

import argparse
import json.decoder
import logging
import os
import requests
import sys
import time
from flask import Flask


class FormatInflux(object):
    def __init__(self, logger, args, weather_data):
        self.logger = logger
        self.args = args
        self.weather_data = weather_data

    def sanitize(self, metric):
        m = str(metric)
        m = m.replace(" ", "_")
        m = m.replace(",", "_")
        return m

    def get_metrics(self):
        self.logger.info("Formatting Influx metrics")
        influx_metrics = []
        tagset = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
            self.sanitize(self.weather_data["macAddress"]),
            self.sanitize(self.weather_data["info"]["name"]),
            self.sanitize(self.weather_data["info"]["coords"]["coords"]["lat"]),
            self.sanitize(self.weather_data["info"]["coords"]["coords"]["lon"]),
            self.sanitize(self.weather_data["info"]["coords"]["address"]),
            self.sanitize(self.weather_data["info"]["coords"]["location"]),
            self.sanitize(self.weather_data["lastData"]["tz"]),
        )
        for k in self.weather_data["lastData"].keys():
            if k not in ["lastRain", "tz", "date"]:
                influx_metrics.append(
                    f"ambientweather_{k},{tagset} value={self.weather_data['lastData'][k]} {time.time_ns()}"
                )
        self.logger.info(f"Returning {len(influx_metrics)} metrics for Influx")
        return influx_metrics

    def create_database(self):
        self.logger.info(
            f"Creating InfluxDB database {self.args.influx_host}:{self.args.influx_port}/{self.args.influx_db}"
        )
        r = requests.post(
            f"http://{self.args.influx_host}:{self.args.influx_port}/query",
            data={"q": f"CREATE DATABASE {self.args.influx_db}"},
        )
        status_code = r.status_code
        if status_code != requests.codes.ok:
            f"Got a {status_code} from InfluxDB at {self.args.influx_host}:{self.args.influx_port}/{self.args.influx_db}; creating the database"
        else:
            f"Created Influx database {self.args.influx_host}:{self.args.influx_port}/{self.args.influx_db}"

    def post_metrics(self):
        self.logger.info("Sending Influx metrics")
        influx_metrics = self.get_metrics()
        for metric in influx_metrics:
            self.logger.info(metric)
            r = requests.post(
                f"http://{self.args.influx_host}:{self.args.influx_port}/write?db={self.args.influx_db}",
                data=metric,
            )
            status_code = r.status_code
            if status_code != 204:
                if status_code == 404:
                    self.logger.info(
                        f"Got a {status_code} from InfluxDB at {self.args.influx_host}:{self.args.influx_port}/{self.args.influx_db}; create the database"
                    )
                else:
                    self.logger.info(
                        f"Got a {status_code} from InfluxDB at {self.args.influx_host}:{self.args.influx_port}/{self.args.influx_db}; {metric}"
                    )
            else:
                self.logger.info(
                    f"Sent {metric} to InfluxDB at {self.args.influx_host}:{self.args.influx_port}/{self.args.influx_db}"
                )


class FormatPrometheus(object):
    def __init__(self, logger, args, weather_data):
        self.logger = logger
        self.args = args
        self.weather_data = weather_data

    def get_metrics(self):
        self.logger.info("Formatting Prometheus metrics")
        prom_metrics = []
        labels = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
            self.weather_data["macAddress"],
            self.weather_data["info"]["name"],
            self.weather_data["info"]["coords"]["coords"]["lat"],
            self.weather_data["info"]["coords"]["coords"]["lon"],
            self.weather_data["info"]["coords"]["address"],
            self.weather_data["info"]["coords"]["location"],
            self.weather_data["lastData"]["tz"],
        )
        for k in self.weather_data["lastData"].keys():
            if k not in ["lastRain", "tz", "date"]:
                prom_metrics.append(
                    "ambientweather_{}{{{}}} {}".format(
                        k, labels, self.weather_data["lastData"][k]
                    )
                )
        self.logger.info(f"Returning {len(prom_metrics)} metrics for Prometheus")
        return prom_metrics


class AmbientWeather(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args

    def fetch_weather(self):
        self.logger.info("Fetching data from AmbientWeather")
        self.r = requests.get(
            f"https://api.ambientweather.net/v1/devices?applicationKey={self.args.ambi_app_key}&apiKey={self.args.ambi_api_key}"
        )
        status_code = self.r.status_code
        if status_code != requests.codes.ok:
            self.logger.error(
                f"Got a {status_code} from AmbientWeather; check your AmbientWeather application and API keys"
            )
        else:
            try:
                weather_data = self.r.json()
                if len(weather_data) == 1:
                    self.logger.info("Got a row of data from AmbientWeather")
                    return weather_data[0]
                else:
                    self.logger.error(
                        f"Didn't get a single result from AmbientWeather (got {len(weather_data)} results)"
                    )
            except json.decoder.JSONDecodeError:
                self.logger.error("Could not decode AmbientWeather result into JSON")
                raise


class SetupLogger(object):
    def __init__(self):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.logger = logging.getLogger("ambientweather-exporter")

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)


class GetArgs(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "--listen-on",
            help="IP address to listen on (default $LISTEN_ON if set, else, '0.0.0.0')",
            default=os.getenv("LISTEN_ON", "0.0.0.0"),
        )
        self.parser.add_argument(
            "--listen-port",
            help="Port to listen on (default 10102)",
            type=int,
            default=os.getenv("LISTEN_PORT", 10102),
        )
        self.parser.add_argument(
            "--ambi-app-key",
            help="AmbientWeather application key",
            default=os.getenv("AMBI_APP_KEY"),
        )
        self.parser.add_argument(
            "--ambi-api-key",
            help="AmbientWeather API key",
            default=os.getenv("AMBI_API_KEY"),
        )
        self.parser.add_argument(
            "--influx-enable",
            help="Enable InfluxDB exporting (default False)",
            action="store_true",
            default=os.getenv("INFLUX_ENABLE", False),
        )
        self.parser.add_argument(
            "--influx-host",
            help="InfluxDB host (default 'influxdb')",
            default=os.getenv("INFLUX_HOST", "influxdb"),
        )
        self.parser.add_argument(
            "--influx-port",
            help="InfluxDB port (default 8086)",
            type=int,
            default=os.getenv("INFLUX_PORT", 8086),
        )
        self.parser.add_argument(
            "--influx-db",
            help="InfluxDB database (default 'ambientweather')",
            default=os.getenv("INFLUX_DB", "ambientweather"),
        )
        self.parser.add_argument(
            "--influx-interval",
            help="InfluxDB sending interval in seconds (default 300)",
            type=int,
            default=os.getenv("INFLUX_INTERVAL", 300),
        )
        self.args = self.parser.parse_args()

    @property
    def listen_on(self):
        return self.args.listen_on

    @property
    def listen_port(self):
        return self.args.listen_port

    @property
    def ambi_app_key(self):
        return self.args.ambi_app_key

    @property
    def ambi_api_key(self):
        return self.args.ambi_api_key

    @property
    def influx_enable(self):
        return self.args.influx_enable

    @property
    def influx_host(self):
        return self.args.influx_host

    @property
    def influx_port(self):
        return self.args.influx_port

    @property
    def influx_db(self):
        return self.args.influx_db

    @property
    def influx_interval(self):
        return self.args.influx_interval


class RunInflux(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args
        self.influx_host = self.args.influx_host
        self.influx_port = self.args.influx_port
        self.influx_interval = self.args.influx_interval
        self.logger.info("Starting Influx shipper")
        self.aw = AmbientWeather(logger, args)
        self.ping()
        self.ship()

    def ping(self):
        try:
            ping_endpoint = f"http://{self.influx_host}:{self.influx_port}/ping"
            r = requests.get(ping_endpoint)
            status_code = r.status_code
            if status_code != 204:
                self.logger.error(
                    f"Unhappy {status_code} from Influx at {ping_endpoint}"
                )
                sys.exit(1)
            else:
                self.logger.info(f"Happy {status_code} from Influx at {ping_endpoint}")
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            self.logger.error(f"Could not connect to Influx at {ping_endpoint}")
            raise SystemExit(e)

    def ship(self):
        if self.influx_interval < 0:
            self.logger.error("Influx sleep interval cannot be negative")
        elif self.influx_interval == 0:
            self.logger.error("Influx sleep interval is zero")
        else:
            self.logger.info(
                f"Shipping Influx metrics every {self.influx_interval} seconds"
            )
            influx = FormatInflux(self.logger, self.args, None)
            influx.create_database()
            while True:
                self.logger.info(
                    f"Sleeping for {self.args.influx_interval} seconds before shipping to Influx"
                )
                time.sleep(self.influx_interval)
                weather_data = self.aw.fetch_weather()
                influx = FormatInflux(self.logger, self.args, weather_data)
                influx.post_metrics()


class RunPrometheus(object):
    def __init__(self, logger, args):
        self.app = Flask(__name__)
        self.logger = logger
        self.args = args
        self.aw = AmbientWeather(logger, args)
        self.logger.info("Starting Prometheus exporter")

        @self.app.route("/")
        @self.app.route("/metrics")
        def prometheus():
            self.logger.info("Prometheus metrics requested")
            weather_data = self.aw.fetch_weather()
            prom = FormatPrometheus(self.logger, self.args, weather_data)
            metrics = prom.get_metrics()
            self.logger.info(f"Prometheus scraped {len(metrics)} metrics from us")
            return "\n".join(metrics) + "\n"

        self.app.run(debug=True, host=self.args.listen_on, port=self.args.listen_port)


if __name__ == "__main__":
    logger = SetupLogger()
    args = GetArgs()
    if args.influx_enable:
        RunInflux(logger, args)
    else:
        RunPrometheus(logger, args)
