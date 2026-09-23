#!/usr/bin/env python3

"""
Upload the latest observation of each station to Windy.com

Uses the Windy Stations API v2: every station is registered at
https://stations.windy.com and has its own station ID and password, stored in
the `windy_id` and `windy_password` columns of the `stations` table.
"""

import argparse
import json
import logging
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timedelta, timezone
from time import sleep


WINDY_UPDATE_URL = 'https://stations.windy.com/pws/v2/observation/update'
# Windy accepts at most one update per station every 5 minutes
UPDATE_INTERVAL = 360
# Windy rejects observations older than 2 hours
MAX_OBSERVATION_AGE = timedelta(hours=2)
DATEUTC_FMT = '%Y-%m-%d %H:%M:%S'

# windy_observations column -> Windy API parameter
PARAMS = {
    'dateutc': 'dateutc',
    'temp': 'temp',
    'dewpoint': 'dewpoint',
    'windspeedmph': 'windspeedmph',
    'winddir': 'winddir',
    'windgustmph': 'windgustmph',
    'rh': 'humidity',
    'uv': 'uv',
    'rainin': 'rainin',
    'baromin': 'baromin',
}


def get_observations():
    db = sqlite3.connect(os.getenv('STATIONS_DB', 'stations.db'))
    db.row_factory = sqlite3.Row
    try:
        return db.execute("""
        SELECT s.windy_id, s.windy_password, o.*
        FROM windy_observations o JOIN stations s ON s.station = o.station
        WHERE s.windy_id IS NOT NULL AND s.windy_password IS NOT NULL
        """).fetchall()
    except sqlite3.Error:
        logging.exception("Unable to retrieve stations and/or observation data")
        return []
    finally:
        db.close()


def upload_observation(observation):
    params = {'id': observation['windy_id']}
    for column, param in PARAMS.items():
        if observation[column] is not None:
            params[param] = observation[column]

    url = f'{WINDY_UPDATE_URL}?{urllib.parse.urlencode(params)}'
    r = urllib.request.Request(url,
                               headers={
                                   'Authorization': f"Bearer {observation['windy_password']}"
                               },
                               method='GET')
    logging.debug("WINDY DATA: %s", params)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            logging.info("Station %s: Windy update %s",
                         observation['station'], resp.status)
            logging.debug("WINDY RESPONSE: %s", resp.read().decode('utf8'))
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf8', 'replace')
        if e.code == 409:
            logging.info("Station %s: observation already uploaded",
                         observation['station'])
            return True
        if e.code == 429:
            try:
                retry_after = json.loads(body).get('retry_after')
            except ValueError:
                retry_after = None
            logging.warning("Station %s: Windy rate limit hit, retry after %s",
                            observation['station'], retry_after)
        else:
            logging.error("Station %s: Windy update failed %s: %s",
                          observation['station'], e.code, body)
    except (urllib.error.URLError, OSError):
        logging.exception("Station %s: cannot upload data to Windy!",
                          observation['station'])
    return False


def _windy(uploaded):
    """
    Upload new observations. `uploaded` maps station -> dateutc of the last
    observation accepted by Windy, so the same observation isn't sent twice.
    """
    now = datetime.now(timezone.utc)
    for observation in get_observations():
        station = observation['station']
        dateutc = observation['dateutc']
        if uploaded.get(station) == dateutc:
            logging.debug("Station %s: no new observation", station)
            continue
        try:
            observed = datetime.strptime(dateutc, DATEUTC_FMT).replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            logging.warning("Station %s: invalid observation time %r", station, dateutc)
            continue
        if now - observed > MAX_OBSERVATION_AGE:
            logging.warning("Station %s: observation from %s is too old for Windy",
                            station, dateutc)
            continue
        if upload_observation(observation):
            uploaded[station] = dateutc


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            prog='update_windy',
            description='Upload latest station observations to Windy.com')
    parser.add_argument('--log', help="Log level", default='DEBUG')
    parser.add_argument('--once', help="Upload once and exit",
                        action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper())

    uploaded = {}
    while True:
        _windy(uploaded)
        if args.once:
            break
        sleep(UPDATE_INTERVAL)
