#!/bin/bash
export HOST_IP=<IP>
cd /home/ubuntu/microservice
docker-compose scale changeservice=0
docker rm $(docker ps -q -f status=exited)
docker rmi -f <image_name> && docker pull <image_name>:latest && docker-compose up -d --remove-orphans