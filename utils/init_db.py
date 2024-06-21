#!/usr/bin/env python3

import os
import sqlite3
import sys


if __name__ == '__main__':
    db_file = os.getenv('STATIONS_DB', 'db/stations.db')
    if os.path.exists(db_file):
        print("Database exists. Nothing to do here.")
        sys.exit(0)
    db_dir = os.path.dirname(db_file)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    with sqlite3.connect(db_file) as db:
        with open('stations.sql', 'r') as fd:
            db.executescript(fd.read())

