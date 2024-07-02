#!/bin/bash

which screen > /dev/null 2>&1

if [ $? -ne 0 ]; then
	echo "You must install screen."
	exit 1
fi

CONTAINER_ID=$(docker ps |grep windy-transform | cut -f1 -d' ')

if [ ! "$CONTAINER_ID" ]; then
	echo "No windy-transform container found."
	exit 2
fi

screen -ls | grep windy-transform
if [ $? -ne 0 ]; then
	screen -dmS windy-transform-${CONTAINER_ID} docker attach ${CONTAINER_ID}
fi

screen -r windy-transform-${CONTAINER_ID}
