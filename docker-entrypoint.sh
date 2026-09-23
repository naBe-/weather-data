#!/bin/bash

service nginx start
source config/default
uwsgi --uid www-data uwsgi_windy_transform.ini
