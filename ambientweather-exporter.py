#!/usr/bin/env python3

import os
import sys
import json
import requests
import subprocess

from flask import Flask
app = Flask(__name__)


applicationKey = os.getenv('AMBI_APP_KEY')
apiKey         = os.getenv('AMBI_API_KEY')


@app.route('/')
@app.route('/metrics')
def prometheus():
    return(ambientweatherPrometheus())


@app.route('/influx')
@app.route('/influxdb')
def influx():
    return(ambientweatherInflux())


def getData():
    global applicationKey, apiKey
    try:
        r = requests.get(f'https://api.ambientweather.net/v1/devices?applicationKey={applicationKey}&apiKey={apiKey}')
        return(r.json()[0])
    except Exception as e:
        print("Couldn't fetch AmbientWeather data, bailing!")
        sys.exit(1)


def ambientweatherPrometheus():
    retn = []
    data = getData()
    try:
        labels = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
            data['macAddress'],
            data['info']['name'],
            data['info']['coords']['coords']['lat'],
            data['info']['coords']['coords']['lon'],
            data['info']['coords']['address'],
            data['info']['coords']['location'],
            data['lastData']['tz']
        )
        for k in data['lastData'].keys():
            if k not in ['lastRain', 'tz', 'date']:
                retn.append('ambientweather_{}{{{}}} {}'.format(k, labels, data['lastData'][k]))
    except Exception as e:
        retn.append(e)
    return("\n".join(retn))


def ambientweatherInflux():
    retn = []
    data = getData()
    try:
        tagset = 'macAddress={},name={},lat={},lon={},address={},location={},tz={}'.format(
            data['macAddress'],
            data['info']['name'],
            data['info']['coords']['coords']['lat'],
            data['info']['coords']['coords']['lon'],
            data['info']['coords']['address'],
            data['info']['coords']['location'],
            data['lastData']['tz']
        )
        for k in data['lastData'].keys():
            if k not in ['lastRain', 'tz', 'date']:
                # retn.append('ambientweather,{} {}={}'.format(tagset, k, data['lastData'][k]))
                retn.append('ambientweather {}={}'.format(k, data['lastData'][k]))
    except Exception as e:
        retn.append(e)
    return("\n".join(retn))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10102)
