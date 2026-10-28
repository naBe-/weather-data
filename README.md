# Transform data from weather stations and upload it to Windy.com

## Windy setup

Uploads use the Windy Stations API v2, which authenticates each station
separately.

1. Register each station at https://stations.windy.com ("My Stations"). Location,
   elevation and sensor heights are configured there.
2. Link the local station to its Windy station ID and password:

   ```
   python3 utils/init_db.py                      # adds the Windy columns to an existing DB
   python3 utils/set_windy_station.py <local station id> <windy station id>
   ```

3. Run `utils/update_windy.py` (`--once` for a single upload). It uploads each
   station's latest observation every 6 minutes. Windy accepts one update per
   station every 5 minutes, and rejects observations older than 2 hours.

## Configuration

`config/default` holds shared settings and loads `config/local` if it exists.
Put credentials and instance-specific settings in `config/local` (not tracked
by git); start from `config/local.example`.

## Read API

The latest upload of each station is available as JSON, in metric units,
under `/api` (port 8080 with the provided `docker-compose.yml`):

- `GET /api/stations`: list of stations,
  `[{"station": 1, "name": "Garden", "has_data": true}, ...]`
- `GET /api/stations/<id>`: latest observation of a station:

  ```json
  {
    "station": 1,
    "name": "Garden",
    "dateutc": "2026-10-28T18:00:00Z",
    "age": 42,
    "outdoor": {
      "temperature": 10.0, "humidity": 80.0, "dewpoint": 6.7,
      "pressure": 1015.9, "wind_speed": 0.4, "wind_gust": 0.9,
      "wind_dir": 90.0, "rain_rate": 0.0, "rain_daily": 0.0,
      "uv": 1.0, "solar_radiation": 23.5
    },
    "indoor": {
      "temperature": 21.1, "humidity": 50.0, "dewpoint": 10.3,
      "pressure": 1015.9
    }
  }
  ```

  Units: °C, %, hPa, m/s, degrees, mm/h, mm, W/m². `age` is the number of
  seconds since the observation. `outdoor` or `indoor` is `null` when the
  station has no such sensor, and a value is `null` when the station doesn't
  report it. Returns 404 for an unknown station or one that hasn't sent data
  yet.

The values come from `logs/station_<id>.data`, the raw latest upload, since
the database only keeps the values sent to Windy. The API has no
authentication: anyone who can reach the server can read the observations.
Station keys and passkeys are never returned.
