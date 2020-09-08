#!/usr/bin/env python3

import os
import sys
import json
import requests
import subprocess

from flask import Flask
app = Flask(__name__)


@app.route('/')
@app.route('/metrics')
def hello():
    data = ambientweather()
    return(data)


def ambientweather():
    data = []
    try:
        applicationKey = os.getenv('AMBI_APP_KEY')
        apiKey         = os.getenv('AMBI_API_KEY')
        r = requests.get(f'https://api.ambientweather.net/v1/devices?applicationKey={applicationKey}&apiKey={apiKey}')
        results = r.json()[0]
        labels = 'macAddress="{}",name="{}",lat="{}",lon="{}",address="{}",location="{}",tz="{}"'.format(
            results['macAddress'],
            results['info']['name'],
            results['info']['coords']['coords']['lat'],
            results['info']['coords']['coords']['lon'],
            results['info']['coords']['address'],
            results['info']['coords']['location'],
            results['lastData']['tz']
        )
        for k in results['lastData'].keys():
            if k not in ['lastRain', 'tz', 'date']:
                data.append('ambientweather_{}{{{}}} {}'.format(k, labels, results['lastData'][k]))
    except Exception as e:
        data.append(e)
    return("\n".join(data))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10102)
