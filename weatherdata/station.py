import logging
import os
import sqlite3


from weatherdata.calc.dewpoint import dew_point


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
        ON CONFLICT(unique_observation) DO UPDATE SET
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

