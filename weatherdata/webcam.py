import cv2
import logging
import os
import sqlite3
import sys

from PIL import Image, ImageDraw, ImageFont
from time import sleep


WINFO = "{} \n\
{}\nt: {}°C / RH: {}%"
RETRY_LIMIT = 3


def capture_image(webcam):
    capture = cv2.VideoCapture(url)
    while True:
        ret, frame = capture.read()
        color_converted = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(color_converted)
        base = Image.open(latest_file).convert('RGBA')
        txt = Image.new('RGBA', base.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype('dejavu.ttf', 10)
        drw = ImageDraw.Draw(txt)
        drw.rectangle([(0, 0), (140, 45)], fill=(0, 0, 0, 128))
        timestamp = datetime.datetime.now() + datetime.timedelta(hours=1)
        weather_data[0] = timestamp.strftime(DATE_FMT)
        drw.text((10, 0), WINFO.format(*weather_data[:3]), font=fnt,
                 fill=(255, 255, 255, 200))
        out = Image.alpha_composite(base, txt)

        update_time = datetime.now()

        db = sqlite3.connect(os.getenv('STATIONS_DB', 'stations.db'))
        db.row_factory = sqlite3.Row
        stations = []
        observations = []
        try:
            station = webcam['station']
            observation = db.execute("SELECT * FROM windy_observations WHERE station=?", (station)).fetchone()
            for inspect in stations_db:
                station = {k: inspect[k] for k in inspect.keys()}
                del station['key']
                stattions.append(station)
            for inspect in observations_db:
                observation = {k: inspect[k] for k in inspect.keys()}
                observations.append(observation)
        except sqlite3.Error:
            logging.exception("Unable to retrieve stations and/or observation data")
        finally:
            db.close()



        image.show()
        sleep(1)



def get_image(webcam_id, webcam_key):
    db = sqlite3.connect(os.getenv('STATIONS_DB', 'stations.db'))
    try:
       image = db.execute("SELECT image FROM webcams WHERE key=? and webcam=?", (webcam_key, webcam_id)).fetchone()
       return image
    except sqlite3.Error as e:
        logging.exception("Unable to retrieve webcam data from database")
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

