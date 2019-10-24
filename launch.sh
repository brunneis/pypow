#!/bin/bash
source env.sh
docker build -t pypow .
docker rm -f pypow 2>&1 > /dev/null
docker run -td -e MINER_NAME=$MINER_NAME --name pypow pypow -k $KAFKA_ENDPOINT
