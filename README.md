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
