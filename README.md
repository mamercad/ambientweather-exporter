# ambientweather-exporter

Simple Python/Flask exporter for [AmbientWeather](https://ambientweather.net) that can be scraped by [Prometheus](https://prometheus.io). With that said, you'll need `flask` installed...

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
