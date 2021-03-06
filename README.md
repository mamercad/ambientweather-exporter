# ambientweather-exporter

Simple Python/Flask exporter for [AmbientWeather](https://ambientweather.net) that can be scraped by [Prometheus](https://prometheus.io). With that said, you'll need `flask` installed. I've also added support for pushing to [InfluxDB](https://www.influxdata.com/products/influxdb-overview/), but, I haven't tested it, let me know (you can set `$INFLUX_HOST` and `$INFLUX_PORT` to override the defaults, `influxdb` and `8086`, respectively). The endpoints `/influx` or `/influxdb` will trigger the sending.

## Environment variables

Read up on this [here](https://ambientweather.docs.apiary.io/#introduction/authentication) and then:

```bash
$ export AMBI_API_KEY=<REDACTED>
$ export AMBI_APP_KEY=<REDACTED>
$ ./ambientweather-exporter.py
* Serving Flask app "ambientweather-exporter" (lazy loading)
* Environment: production
WARNING: This is a development server. Do not use it in a production deployment.
Use a production WSGI server instead.
* Debug mode: on
* Running on http://0.0.0.0:10102/ (Press CTRL+C to quit)
* Restarting with stat
* Debugger is active!
* Debugger PIN: 150-675-683
127.0.0.1 - - [08/Sep/2020 16:49:10] "GET / HTTP/1.1" 200 -
```

From a client:

```bash
$ curl -s http://localhost:10102 2>&1 | tail -3
ambientweather_dewPoint{macAddress="REDACTED",name="CLOUDMASON",lat="REDACTED",lon="REDACTED",address="REDACTED",location="REDACTED",tz="America/Detroit"} 53.01
ambientweather_feelsLikein{macAddress="REDACTED",name="CLOUDMASON",lat="REDACTED",lon="REDACTED",address="REDACTED",location="REDACTED",tz="America/Detroit"} 67.3
ambientweather_dewPointin{macAddress="REDACTED",name="CLOUDMASON",lat="REDACTED",lon="REDACTED",address="REDACTED",location="REDACTED",tz="America/Detroit"} 49.6
```

## Grafana:

![Screenshot](ambientweather-screenshot.png)

Panel JSON:

```json
{
  "fieldConfig": {
    "defaults": {
      "custom": {},
      "unit": "fahrenheit",
      "min": 0,
      "max": 100,
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "green",
            "value": null
          },
          {
            "color": "super-light-blue",
            "value": 10
          },
          {
            "color": "light-blue",
            "value": 20
          },
          {
            "color": "semi-dark-blue",
            "value": 30
          },
          {
            "color": "super-light-green",
            "value": 40
          },
          {
            "color": "light-green",
            "value": 50
          },
          {
            "color": "dark-green",
            "value": 60
          },
          {
            "color": "light-orange",
            "value": 70
          },
          {
            "color": "semi-dark-orange",
            "value": 80
          },
          {
            "color": "dark-orange",
            "value": 90
          },
          {
            "color": "dark-red",
            "value": 100
          }
        ]
      },
      "mappings": []
    },
    "overrides": []
  },
  "gridPos": {
    "h": 9,
    "w": 6,
    "x": 0,
    "y": 0
  },
  "id": 2,
  "options": {
    "reduceOptions": {
      "values": false,
      "calcs": [
        "last"
      ],
      "fields": ""
    },
    "showThresholdLabels": true,
    "showThresholdMarkers": true
  },
  "pluginVersion": "7.1.5",
  "targets": [
    {
      "expr": "ambientweather_feelsLike",
      "interval": "",
      "legendFormat": " ",
      "refId": "A"
    }
  ],
  "timeFrom": null,
  "timeShift": null,
  "title": "Feels Like",
  "transparent": true,
  "type": "gauge",
  "datasource": null
}
```
