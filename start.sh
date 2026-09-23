#!/bin/bash

source config/default

docker image ls|grep windy-transform > /dev/null 2>&1
if [ $? -ne 0 ]; then
	docker build -t windy-transform .
fi

docker compose up -d
