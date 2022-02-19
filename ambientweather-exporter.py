#!/usr/bin/env python3

import json.decoder
import logging
import os
import requests
import sys
import time

from flask import Flask

app = Flask(__name__)


listen_on = "0.0.0.0"
listen_port = os.getenv("EXPORTER_PORT", "10102")
ambi_app_key = os.getenv("AMBI_APP_KEY")
ambi_api_key = os.getenv("AMBI_API_KEY")
influx_host = os.getenv("INFLUX_HOST", "influxdb")
influx_port = os.getenv("INFLUX_PORT", "8086")
influx_db = os.getenv("INFLUX_DB", "ambientweather")

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
)
logger = logging.getLogger("ambientweather-exporter")


@app.route("/")
@app.route("/metrics")
def prometheus():
    metrics = ambientweather_prometheus()
    logger.info(f"Prometheus scraped {len(metrics)} metrics from us")
    return "\n".join(metrics) + "\n"


@app.route("/influx")
@app.route("/influxdb")
def influx():
    metrics = ambientweather_influx()
    logger.info(f"Shipped {len(metrics)} metrics to InfluxDB")
    for metric in metrics:
        r = requests.post(
            f"http://{influx_host}:{influx_port}/write?db={influx_db}", data=metric
        )
        status_code = r.status_code
        if status_code != requests.codes.ok:
            raise Exception(
                f"Got a {status_code} from InfluxDB at {influx_host}:{influx_port}"
            )


def get_ambientweather_data():
    logger.info("Fetching data from AmbientWeather")
    global ambi_app_key, ambi_api_key
    r = requests.get(
        f"https://api.ambientweather.net/v1/devices?applicationKey={ambi_app_key}&apiKey={ambi_api_key}"
    )
    status_code = r.status_code
    if status_code != requests.codes.ok:
        raise Exception(
            f"Got a {status_code} from AmbientWeather; check your $AMBI_APP_KEY and $AMBI_API_KEY"
        )
    try:
        weather_data = r.json()
        if len(weather_data) == 1:
            logger.info("Got a row of data from AmbientWeather")
            return weather_data[0]
        else:
            logger.error("Not expecting more than one row of data")
    except json.decoder.JSONDecodeError:
        logger.error("Could not decode AmbientWeather into JSON")
        raise


def ambientweather_prometheus():
    logger.info("Collecting Prometheus metrics")
    prom_data = []
    data = get_ambientweather_data()
    labels = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
        data["macAddress"],
        data["info"]["name"],
        data["info"]["coords"]["coords"]["lat"],
        data["info"]["coords"]["coords"]["lon"],
        data["info"]["coords"]["address"],
        data["info"]["coords"]["location"],
        data["lastData"]["tz"],
    )
    for k in data["lastData"].keys():
        if k not in ["lastRain", "tz", "date"]:
            prom_data.append(
                "ambientweather_{}{{{}}} {}".format(k, labels, data["lastData"][k])
            )
    logger.info(f"Returning {len(prom_data)} metrics for Prometheus")
    return prom_data


def ambientweather_influx():
    logger.info("Collecting Influx metrics")
    influx_data = []
    data = get_ambientweather_data()
    tagset = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
        data["macAddress"],
        data["info"]["name"],
        data["info"]["coords"]["coords"]["lat"],
        data["info"]["coords"]["coords"]["lon"],
        data["info"]["coords"]["address"],
        data["info"]["coords"]["location"],
        data["lastData"]["tz"],
    )
    for k in data["lastData"].keys():
        if k not in ["lastRain", "tz", "date"]:
            influx_data.append(
                f"ambientweather_{k},{tagset} value={data['lastData'][k]} {time.time_ns()}"
            )

    logger.info(f"Returning {len(influx_data)} metrics for Influx")
    return influx_data


if __name__ == "__main__":
    if not ambi_app_key or not ambi_api_key:
        raise Exception("Ensure that both $AMBI_APP_KEY and $AMBI_API_KEY are set!")

    logger.info(f"Listening on {listen_on}:{listen_port}")
    logger.info(
        f"Prometheus metrics at http://{listen_on}:{listen_port} or http://{listen_on}:{listen_port}/metrics"
    )
    logger.info(f"InfluxDB destination set as {influx_host}:{influx_port}/{influx_db}")
    logger.info(
        f"Trigger sending to InfluxDB with http://{listen_on}:{listen_port}/influx or http://{listen_on}:{listen_port}/influxdb"
    )

    app.run(debug=True, host=listen_on, port=int(listen_port))
