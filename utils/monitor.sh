#!/bin/bash

which screen > /dev/null 2>&1

if [ $? -ne 0 ]; then
	echo "You must install screen."
	exit 1
fi

CONTAINER_ID=$(docker ps |grep weather-data | cut -f1 -d' ')

if [ ! "$CONTAINER_ID" ]; then
	echo "No weather-data container found."
	exit 2
fi

screen -ls | grep weather-data
if [ $? -ne 0 ]; then
	screen -dmS weather-data-${CONTAINER_ID} docker attach ${CONTAINER_ID}
fi

screen -r weather-data-${CONTAINER_ID}
