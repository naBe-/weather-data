#!/usr/bin/env python3

import json
import logging
import os
import sqlite3
import urllib.request

from datetime import datetime, timedelta, UTC
from time import sleep


def _windy(windy_api_key):
    update_time = datetime.now(UTC)

    db = sqlite3.connect(os.getenv('STATIONS_DB', 'stations.db'))
    db.row_factory = sqlite3.Row
    stations = []
    observations = []
    try:
        stations_db = db.execute("SELECT * FROM stations").fetchall()
        observations_db = db.execute("SELECT * FROM windy_observations").fetchall()
        for inspect in stations_db:
            station = {k: inspect[k] for k in inspect.keys()}
            del station['key']
        for inspect in observations_db:
            observation = {k: inspect[k] for k in inspect.keys()}
    except sqlite3.Error:
        logging.exception("Unable to retrieve stations and/or observation data")
    finally:
        db.close()

    remove_stations = []

    for station in stations:
        observation_found = False
        station_id = station['station']
        for observation in observations:
            if observation['station'] == station_id:
                observation_found = True
                break
        if observation_found is False:
            remove_stations.append(station)

    stations = [i for i in stations if i not in remove_stations]

    if len(stations) < 1:
        return update_time

    payload = {'stations': stations, 'observations': observations}

    url = f'https://stations.windy.com/pws/update/{windy_api_key}'

    try:
        r = urllib.request.Request(url,
                                   data=json.dumps(payload).encode('utf8'),
                                   headers={
                                       'Content-Type': 'application/json'
                                   },
                                   method='POST')
        r = urllib.request.urlopen(r)
        logging.debug("WINDY DATA: ", payload)
        logging.debug("WINDY STATUS: ", r.status)
        logging.debug("WINDY RESPONSE: ", r.read())
        return update_time
    except Exception as e:
        logging.exception('Cannot upload data to Windy!')
        raise e


if __name__ == '__main__':
    windy_api_key = os.environ.get('WINDY_API_KEY')
    while True:
        update_time = os.environ.get('LAST_WINDY_UPDATE')
        if update_time:
            update_time = datetime.strptime(update_time, '%Y-%m-%dT%H:%M:%S')
        if update_time is None or update_time < datetime.utcnow() + timedelta(minutes=5): 
            try:
                update_time = _windy(windy_api_key)
                os.environ['LAST_WINDY_UPDATE'] = update_time.strftime('%Y-%m-%dT%H:%M:%S')
            except Exception:
                pass
            sleep(360)
