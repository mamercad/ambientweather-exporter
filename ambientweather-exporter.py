#!/usr/bin/env python3

import argparse
import json.decoder
import logging
import os
from pydoc import describe
import requests
import sys
import time
from flask import Flask


class FormatInflux(object):
    def __init__(self, logger, args, weather_data):
        self.logger = logger
        self.args = args
        self.weather_data = weather_data

    def get_metrics(self):
        self.logger.info("Formatting Influx metrics")
        influx_metrics = []
        tagset = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
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
                influx_metrics.append(
                    f"ambientweather_{k},{tagset} value={self.weather_data['lastData'][k]} {time.time_ns()}"
                )
        self.logger.info(f"Returning {len(influx_metrics)} metrics for Influx")
        return influx_metrics


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


class RunServer(object):
    def __init__(self, logger, args):
        self.app = Flask(__name__)
        self.logger = logger
        self.args = args
        self.aw = AmbientWeather(logger, args)

        @self.app.route("/")
        @self.app.route("/metrics")
        def prometheus():
            self.logger.info("Prometheus metrics requested")
            weather_data = self.aw.fetch_weather()
            prom = FormatPrometheus(self.logger, self.args, weather_data)
            metrics = prom.get_metrics()
            self.logger.info(f"Prometheus scraped {len(metrics)} metrics from us")
            return "\n".join(metrics) + "\n"

        @self.app.route("/influx")
        @self.app.route("/influxdb")
        def influx():
            self.logger.info("Influx metrics requested")
            weather_data = self.aw.fetch_weather()
            influx = FormatInflux(self.logger, self.args, weather_data)
            metrics = influx.get_metrics()
            self.logger.info(f"Shipped {len(metrics)} metrics to Influx")
            return "\n".join(metrics) + "\n"
            # metrics = ambientweather_influx()
            # logger.info(f"Shipped {len(metrics)} metrics to InfluxDB")
            # for metric in metrics:
            #     r = requests.post(
            #         f"http://{influx_host}:{influx_port}/write?db={influx_db}", data=metric
            #     )
            #     status_code = r.status_code
            #     if status_code != requests.codes.ok:
            #         raise Exception(
            #             f"Got a {status_code} from InfluxDB at {influx_host}:{influx_port}"
            #         )

        self.logger.info("starting")
        self.app.run(debug=True, host=self.args.listen_on, port=self.args.listen_port)


if __name__ == "__main__":
    logger = SetupLogger()
    args = GetArgs()
    ws = RunServer(logger, args)

    # logger.info(f"Listening on {listen_on}:{listen_port}")
    # logger.info(
    #     f"Prometheus metrics at http://{listen_on}:{listen_port} or http://{listen_on}:{listen_port}/metrics"
    # )
    # logger.info(f"InfluxDB destination set as {influx_host}:{influx_port}/{influx_db}")
    # logger.info(
    #     f"Trigger sending to InfluxDB with http://{listen_on}:{listen_port}/influx or http://{listen_on}:{listen_port}/influxdb"
    # )

    # app.run(debug=True, host=listen_on, port=int(listen_port))
