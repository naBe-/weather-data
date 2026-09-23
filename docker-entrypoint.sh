#!/bin/bash

service nginx start
source config/default
python3 utils/init_db.py
uwsgi --uid www-data uwsgi_windy_transform.ini
