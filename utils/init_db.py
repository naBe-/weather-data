#!/usr/bin/env python3

import os
import sqlite3
import sys


SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'db', 'stations.sql')

# Columns added after the initial schema: (table, column, type)
MIGRATIONS = [
    ('stations', 'windy_id', 'TEXT'),
    ('stations', 'windy_password', 'TEXT'),
]


def migrate(db):
    for table, column, col_type in MIGRATIONS:
        columns = [row[1] for row in db.execute(f"PRAGMA table_info({table})")]
        if column not in columns:
            print(f"Adding column {table}.{column}")
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


if __name__ == '__main__':
    db_file = os.getenv('STATIONS_DB', 'db/stations.db')
    if os.path.exists(db_file):
        with sqlite3.connect(db_file) as db:
            migrate(db)
        print("Database exists. Migrations applied.")
        sys.exit(0)
    db_dir = os.path.dirname(db_file)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    with sqlite3.connect(db_file) as db:
        with open(SCHEMA, 'r') as fd:
            db.executescript(fd.read())
