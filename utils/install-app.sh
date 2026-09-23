#!/bin/bash

SCRIPT_DIR=$(cd `dirname $0` && pwd)
PROJECT_DIR=$(dirname $SCRIPT_DIR)

cd "${PROJECT_DIR}"

python3 utils/init_db.py
cp nginx/conf/default /etc/nginx/sites-available/
