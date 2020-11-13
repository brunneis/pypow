#!/bin/bash
while true; do
  docker cp pypow:/opt/catenae/winning_chain.txt .
  clear
  head -24 winning_chain.txt
  sleep 1
done
