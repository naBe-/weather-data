#!/bin/bash

source config/default

# Always build: the code is copied into the image, so an existing image would
# keep running the old version. Unchanged layers come from the build cache.
docker build -t windy-transform .

docker compose up -d
