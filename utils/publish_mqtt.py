import fcntl
import json
import logging
import os
import signal
import sys

from functools import partial
from paho.mqtt import client as mqtt_client
from time import sleep


DATA_FILE = './logs/station_0.data'
TOPIC = 'weather/temperature/in'
MQTT_BROKER = '192.168.3.10'
MQTT_PORT = 1883
USERNAME = 'weatherstation'
PASSWORD = 'xxxxxx'
FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_DELAY = 60


def publish_data(signum, frame, mqtt):
    try:
        with open(DATA_FILE, 'r') as fd:
            data = json.load(fd)
    except Exception as err:
        logging.error("Unable to read JSON: %s", err)
        return

    t_in_c = (float(data['tempinf'][0]) - 32) / 1.8

    try:
        mqtt.publish(TOPIC, str(t_in_c))
        logging.debug("%s > %s", TOPIC, str(t_in_c))
    except Exception as err:
        logging.error("Failed to publish: %s", err)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            logging.info('Connected to MQTT.')
        else:
            logging.info('Unable to connect. Return code: %s', rc)

    def on_disconnect(client, userdata, flags, rc, properties):
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        while True:
            logging.info("<%d> Reconnecting in %d seconds...", reconnect_count, reconnect_delay)
            sleep(reconnect_delay)
            try:
                client.reconnect()
                logging.info("Successfully reconnected.")
                return
            except Exception as err:
                logging.error('%s. Failed to reconnect. Retrying...')
            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(MQTT_BROKER, MQTT_PORT)
    return client


def loop():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    client = connect_mqtt()
    client.loop_start()
    publish = partial(publish_data, mqtt=client)
    signal.signal(signal.SIGIO, publish)
    fd = os.open(os.path.dirname(DATA_FILE), os.O_RDONLY)
    fcntl.fcntl(fd, fcntl.F_SETSIG, 0)
    fcntl.fcntl(fd, fcntl.F_NOTIFY, fcntl.DN_MODIFY | fcntl.DN_CREATE | fcntl.DN_MULTISHOT)
    while True:
        sleep(10)

loop()
