#!/usr/bin/env python3

"""
Link a local station to its Windy.com station

Register the station at https://stations.windy.com first; its station ID and
password are shown on the station detail page in "My Stations".
"""

import argparse
import getpass
import os
import sqlite3
import sys


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            prog='set_windy_station',
            description='Set Windy station ID and password for a local station')
    parser.add_argument('station', help="Local station ID", type=int)
    parser.add_argument('windy_id', help="Windy station ID")
    parser.add_argument('-p', '--password', help="Windy station password "
                        "(prompted for if omitted)", default=None)
    parser.add_argument('-d', '--db', help="SQLite3 database file",
                        default=os.getenv('STATIONS_DB', 'db/stations.db'))

    args = parser.parse_args()

    password = args.password or getpass.getpass("Windy station password: ")

    with sqlite3.connect(args.db) as db:
        cur = db.execute("UPDATE stations SET windy_id=?, windy_password=? WHERE station=?",
                         (args.windy_id, password, args.station))
        db.commit()

    if cur.rowcount == 0:
        print(f"Station {args.station} not found.")
        sys.exit(1)
    print(f"Station {args.station} linked to Windy station {args.windy_id}.")
