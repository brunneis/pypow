#!/bin/bash
source env.sh
docker build -t pypow .

docker rm -f pypow-kafka
docker run -d --net=host --name pypow-kafka catenae/kafka

docker rm -f pypow 2>&1 > /dev/null
docker run -td --net=host -e MINER_NAME=$MINER_NAME --name pypow pypow -k $KAFKA_ENDPOINT
