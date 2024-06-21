#!/bin/bash

service nginx start
uwsgi --uid www-data uwsgi_windy_transform.ini
