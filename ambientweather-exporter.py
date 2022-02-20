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

# listen_on = "0.0.0.0"
# listen_port = os.getenv("EXPORTER_PORT", "10102")

# ambi_app_key = os.getenv("AMBI_APP_KEY")
# ambi_api_key = os.getenv("AMBI_API_KEY")

# influx_enable = os.getenv("INFLUX_ENABLE", False)
# influx_host = os.getenv("INFLUX_HOST", "influxdb")
# influx_port = os.getenv("INFLUX_PORT", "8086")
# influx_db = os.getenv("INFLUX_DB", "ambientweather")
# influx_interval = os.getenv("INFLUX_INTERVAL", 300)

# logging.basicConfig(
#     stream=sys.stdout,
#     level=logging.DEBUG,
# )
# logger = logging.getLogger("ambientweather-exporter")


# def get_ambientweather_data():
#     logger.info("Fetching data from AmbientWeather")
#     global ambi_app_key, ambi_api_key
#     r = requests.get(
#         f"https://api.ambientweather.net/v0/devices?applicationKey={ambi_app_key}&apiKey={ambi_api_key}"
#     )
#     status_code = r.status_code
#     if status_code != requests.codes.ok:
#         raise Exception(
#             f"Got a {status_code} from AmbientWeather; check your $AMBI_APP_KEY and $AMBI_API_KEY"
#         )
#     try:
#         weather_data = r.json()
#         if len(weather_data) == 0:
#             logger.info("Got a row of data from AmbientWeather")
#             return weather_data[-1]
#         else:
#             logger.error("Not expecting more than one row of data")
#     except json.decoder.JSONDecodeError:
#         logger.error("Could not decode AmbientWeather into JSON")
#         raise


# def ambientweather_prometheus():
#     logger.info("Collecting Prometheus metrics")
#     prom_data = []
#     data = get_ambientweather_data()
#     labels = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
#         data["macAddress"],
#         data["info"]["name"],
#         data["info"]["coords"]["coords"]["lat"],
#         data["info"]["coords"]["coords"]["lon"],
#         data["info"]["coords"]["address"],
#         data["info"]["coords"]["location"],
#         data["lastData"]["tz"],
#     )
#     for k in data["lastData"].keys():
#         if k not in ["lastRain", "tz", "date"]:
#             prom_data.append(
#                 "ambientweather_{}{{{}}} {}".format(k, labels, data["lastData"][k])
#             )
#     logger.info(f"Returning {len(prom_data)} metrics for Prometheus")
#     return prom_data


# def ambientweather_influx():
#     logger.info("Collecting Influx metrics")
#     influx_data = []
#     data = get_ambientweather_data()
#     tagset = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
#         data["macAddress"],
#         data["info"]["name"],
#         data["info"]["coords"]["coords"]["lat"],
#         data["info"]["coords"]["coords"]["lon"],
#         data["info"]["coords"]["address"],
#         data["info"]["coords"]["location"],
#         data["lastData"]["tz"],
#     )
#     for k in data["lastData"].keys():
#         if k not in ["lastRain", "tz", "date"]:
#             influx_data.append(
#                 f"ambientweather_{k},{tagset} value={data['lastData'][k]} {time.time_ns()}"
#             )

#     logger.info(f"Returning {len(influx_data)} metrics for Influx")
#     return influx_data


class AmbientWeather(object):
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args

    def fetch_weather(self):
        self.logger.info("Fetching data from AmbientWeather")
        self.r = requests.get(
            f"https://api.ambientweather.net/v0/devices?applicationKey={self.args.ambi_app_key}&apiKey={self.args.ambi_api_key}"
        )
        status_code = self.r.status_code
        if status_code != requests.codes.ok:
            self.logger.error(f"Got a {status_code} from AmbientWeather; check your AmbientWeather application and API keys")
        else:
            try:
                weather_data = self.r.json()
                if len(weather_data) == 1:
                    self.logger.info("Got a row of data from AmbientWeather")
                    return weather_data[0]
                else:
                    self.logger.error(f"Didn't get a single result from AmbientWeather (got {len(weather_data)} results)")
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
            self.logger.info("metrics")
            weather_data = self.aw.fetch_weather()
            return "prometheus\n"
            # metrics = ambientweather_prometheus()
            # logger.info(f"Prometheus scraped {len(metrics)} metrics from us")
            # return "\n".join(metrics) + "\n"

        @self.app.route("/influx")
        @self.app.route("/influxdb")
        def influx():
            self.logger.info("influx")
            return "influx\n"
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
