#!/bin/bash

source config/default

docker image ls|grep weather-data > /dev/null 2>&1
if [ $? -ne 0 ]; then
	docker build -t weather-data .
fi

docker compose up -d
