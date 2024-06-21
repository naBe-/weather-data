#!/usr/bin/env python3

import argparse
import json
import os
import random
import string
import sqlite3
import sys

PROMPT = [
        {'label': 'Station name',
         'type': str,
         'var': 'name'},
        {'label': 'Latitude',
         'type': float,
         'var': 'lat'},
        {'label': 'Longitude',
         'type': float,
         'var': 'lon'},
        {'label': 'Elevation (m)',
         'type': int,
         'var': 'elevation'},
        {'label': 'Height of temperature sensor above the surface (m)',
         'type': int,
         'var': 'tempheight'},
        {'label': 'Height of wind sensor above the surface (m)',
         'type': int,
         'var': 'windheight'},
        ]

def add_station(db_file: str, data: dict, station_id: int=None):
    data_tuple = (data['name'],
       data['lat'],
       data['lon'],
       data['elevation'],
       data['tempheight'],
       data['windheight'])
    key = gen_key()
    with sqlite3.connect(db_file) as db:
        if station_id is not None:
            db.execute("""
            INSERT INTO stations (station, key, name, lat, lon, elevation, tempheight, windheight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (station_id, key, *data_tuple))
        else:
            db.execute("""
            INSERT INTO stations (key, name, lat, lon, elevation, tempheight, windheight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (key, *data_tuple))
        db.commit()
    return station_id, key

def gen_key():
    return ''.join(random.choices(string.digits + string.ascii_letters, k=10))

def prompt():
    data = {}
    for item in PROMPT:
        while item['var'] not in data:
            try:
                value = item['type'](input(f"{item['label']}: "))
                data[item['var']] = value
            except ValueError:
                print(f"Value must be of type {item['type'].__name__}. Try again.")
            except (EOFError, KeyboardInterrupt):
                print()
                print("Bye!")
                sys.exit(2)
    return data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            prog='add_station',
            description='Add weather station to Windy transform database')
    parser.add_argument('-f', '--file', help="Read data from JSON file",
                        default=None)
    parser.add_argument('-d', '--db', help="SQLite3 database file",
                        default=os.getenv('STATIONS_DB', 'db/stations.db'))
    parser.add_argument('-i', '--id', help="Station ID", type=int,
                        default=None)
    
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, 'r') as fd:
            data = json.load(fd)
    else:
        data = prompt()

    db_file = args.db
    station_id = args.id
    
    station_id, key = add_station(db_file, data, station_id)

    print("SUMMARY")
    print()
    print(f"Station ID: {station_id}")
    print(f"Key: {key}")
    for (k, v) in data.items():
        print(f"{k}: {v}")
