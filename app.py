# -*- coding: utf-8 -*-

"""
Transform data from weather station and upload it to Windy.com
"""

import json
import logging
import os
import sqlite3
import urllib.parse

from datetime import datetime, timezone

from weathercalc.dewpoint import dew_point


LOGS_DIR = os.getenv('LOGS_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs'))
DATEUTC_FMT = '%Y-%m-%d %H:%M:%S'


def station_data_file(station_id):
    return os.path.join(LOGS_DIR, f"station_{station_id}.data")


def get_station_info(station_id, station_key):
    db = sqlite3.connect(os.getenv('STATIONS_DB', 'stations.db'))
    db.row_factory = sqlite3.Row
    try:
       station = db.execute("SELECT * FROM stations WHERE key=? and station=?", (station_key, station_id)).fetchone()
       return station
    except sqlite3.Error as e:
        logging.exception("Unable to retrieve data from database")
        return None
    finally:
        if db is not None:
            db.close()

def update_data(station, data):
    tempf = float(data['tempf'][0])
    tempc = round((tempf - 32) / 1.8)
    rh = int(data['humidity'][0])
    dewpoint = dew_point(tempc, rh)
    windspeedmph =float(data['windspeedmph'][0])
    winddir = int(data['winddir'][0])
    windgustmph = float(data['windgustmph'][0])
    uv = int(data['uv'][0])
    rainin = float(data['hourlyrainin'][0])
    baromin = float(data['baromrelin'][0])
    observations = (data['dateutc'][0], tempc, dewpoint,
                    windspeedmph, winddir, windgustmph,
                    rh, uv, rainin, baromin)
    db = sqlite3.connect(os.getenv('STATIONS_DB', 'stations.db'))
    try:
        db.execute("""
        INSERT INTO windy_observations (
        station, dateutc, temp, dewpoint, windspeedmph, winddir, windgustmph,
        rh, uv, rainin, baromin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(station) DO UPDATE SET
        dateutc=?, temp=?, dewpoint=?,
        windspeedmph=?, winddir=?, windgustmph=?,
        rh=?, uv=?, rainin=?, baromin=?
        """,
        (station['station'], *observations, *observations))
        db.commit()
    except sqlite3.Error:
        logging.exception("Unable to update Windy obsevation data")
    finally:
        db.close()

def windy_transform(env, start_response):
    path = env['PATH_INFO'].split('/')
    station_key = path[-1]
    station_id = path[-2]
    station_info = get_station_info(station_id, station_key)

    if not station_info:
        start_response('404 Station Not Found', [('Content-Type', 'text/plain')])
        return [b'STATION NOT IDENTIFIED']

    data = urllib.parse.parse_qs(env['wsgi.input'].readline().decode(), True)
    # Write to a temporary file and rename, so readers (weather_api,
    # publish_mqtt) never see a half written file.
    data_file = station_data_file(station_id)
    try:
        with open(f"{data_file}.tmp", "w") as fd:
            json.dump(data, fd)
        os.replace(f"{data_file}.tmp", data_file)
    except OSError:
        logging.exception("Unable to save data of station %s to %s", station_id, data_file)
    logging.debug("DATA RCVD: %s", data)
    
    try:
        update_data(station_info, data)
    except KeyError as kerr:
        logging.exception("Key not found: %s", kerr)
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return [b'BAD INPUT DATA']

    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'KO']


# --- Read API -------------------------------------------------------------
#
# Serves the latest upload of each station in metric units:
#
#   GET /api/stations       list of stations
#   GET /api/stations/<id>  latest observation of a station
#
# Values come from logs/station_<id>.data (the raw upload), because the
# database only keeps outdoor values, rounded for Windy.

def _value(data, key):
    try:
        return float(data[key][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def _convert(value, factor, digits=1, offset=0):
    if value is None:
        return None
    return round((value + offset) * factor, digits)


def _temp_c(data, key):
    return _convert(_value(data, key), 1 / 1.8, offset=-32)


def _dewpoint(temp, rh):
    if temp is None or not rh:
        return None
    try:
        return round(dew_point(temp, rh), 1)
    except ValueError:
        return None


def _outdoor(data):
    temp = _temp_c(data, 'tempf')
    if temp is None:
        return None
    rh = _value(data, 'humidity')
    return {
        'temperature': temp,                                        # °C
        'humidity': rh,                                             # %
        'dewpoint': _dewpoint(temp, rh),                            # °C
        'pressure': _convert(_value(data, 'baromrelin'), 33.8639),  # hPa
        'wind_speed': _convert(_value(data, 'windspeedmph'), 0.44704),  # m/s
        'wind_gust': _convert(_value(data, 'windgustmph'), 0.44704),    # m/s
        'wind_dir': _value(data, 'winddir'),                        # degrees
        'rain_rate': _convert(_value(data, 'rainratein'), 25.4),    # mm/h
        'rain_daily': _convert(_value(data, 'dailyrainin'), 25.4),  # mm
        'uv': _value(data, 'uv'),
        'solar_radiation': _value(data, 'solarradiation'),          # W/m²
    }


def _indoor(data):
    temp = _temp_c(data, 'tempinf')
    if temp is None:
        return None
    rh = _value(data, 'humidityin')
    return {
        'temperature': temp,                                        # °C
        'humidity': rh,                                             # %
        'dewpoint': _dewpoint(temp, rh),                            # °C
        'pressure': _convert(_value(data, 'baromrelin'), 33.8639),  # hPa
    }


def _observation(station):
    try:
        with open(station_data_file(station['station']), 'r') as fd:
            data = json.load(fd)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        logging.exception("Unable to read data of station %s", station['station'])
        return None

    dateutc = None
    age = None
    try:
        observed = datetime.strptime(data['dateutc'][0], DATEUTC_FMT).replace(tzinfo=timezone.utc)
        dateutc = observed.strftime('%Y-%m-%dT%H:%M:%SZ')
        age = max(0, int((datetime.now(timezone.utc) - observed).total_seconds()))
    except (KeyError, IndexError, ValueError):
        pass

    return {
        'station': station['station'],
        'name': station['name'],
        'dateutc': dateutc,  # ISO 8601, UTC
        'age': age,          # seconds since the observation
        'outdoor': _outdoor(data),
        'indoor': _indoor(data),
    }


def _stations(station_id=None):
    db = sqlite3.connect(os.getenv('STATIONS_DB', 'stations.db'))
    db.row_factory = sqlite3.Row
    try:
        if station_id is None:
            return db.execute("SELECT station, name FROM stations ORDER BY station").fetchall()
        return db.execute("SELECT station, name FROM stations WHERE station=?", (station_id,)).fetchall()
    finally:
        db.close()


def _json_response(start_response, status, body):
    payload = json.dumps(body).encode()
    start_response(status, [('Content-Type', 'application/json'),
                            ('Content-Length', str(len(payload))),
                            ('Cache-Control', 'no-store')])
    return [payload]


def weather_api(env, start_response):
    if env['REQUEST_METHOD'] not in ('GET', 'HEAD'):
        return _json_response(start_response, '405 Method Not Allowed',
                              {'error': 'Method not allowed'})

    # PATH_INFO is relative to the /api mount point, but accept the full path
    # as well in case the server does not strip it.
    path = [p for p in env.get('PATH_INFO', '').split('/') if p]
    if path[:1] == ['api']:
        path = path[1:]

    try:
        if path == ['stations']:
            stations = [{'station': s['station'], 'name': s['name'],
                         'has_data': os.path.exists(station_data_file(s['station']))}
                        for s in _stations()]
            return _json_response(start_response, '200 OK', stations)

        if len(path) == 2 and path[0] == 'stations':
            try:
                station_id = int(path[1])
            except ValueError:
                return _json_response(start_response, '400 Bad Request',
                                      {'error': 'Station ID must be a number'})
            stations = _stations(station_id)
            if not stations:
                return _json_response(start_response, '404 Not Found',
                                      {'error': 'Station not found'})
            observation = _observation(stations[0])
            if observation is None:
                return _json_response(start_response, '404 Not Found',
                                      {'error': 'No data received from this station yet'})
            return _json_response(start_response, '200 OK', observation)
    except sqlite3.Error:
        logging.exception("Unable to retrieve data from database")
        return _json_response(start_response, '500 Internal Server Error',
                              {'error': 'Database error'})

    return _json_response(start_response, '404 Not Found', {'error': 'Not found'})
