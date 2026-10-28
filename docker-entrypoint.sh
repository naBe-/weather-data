#!/bin/bash

source config/default
service nginx start
python3 utils/init_db.py
# uWSGI runs as www-data. SQLite needs write access to the database and to its
# directory (journal file). Grant it through the group to keep host ownership.
STATIONS_DB_DIR=$(dirname $STATIONS_DB)
chgrp www-data $STATIONS_DB_DIR $STATIONS_DB
chmod g+w $STATIONS_DB_DIR $STATIONS_DB
# Same for logs/, where the latest upload of each station is saved for the
# read API and publish_mqtt. It is bind mounted, so the chown in the
# Dockerfile does not apply to it.
mkdir -p logs
chgrp -R www-data logs
chmod -R g+w logs
uwsgi --uid www-data uwsgi_windy_transform.ini
