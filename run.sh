#!/bin/bash

if ! command -v docker &> /dev/null; then
    echo "You should install Docker: https://docs.docker.com/get-started/get-docker"
    exit 1
fi

SCRIPT_DIR=`dirname $(realpath -m "$0")`
CONTAINER_NAME="vasiniyo-chat-bot"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OS" == "Windows_NT" ]]; then
    VOLUME_PATH="$(pwd -W)/data"
    LOG_PATH="$(pwd -W)/logs"
    "MM/dd/yyyy HH:mm:ss"
    LOG_FILE="$LOG_PATH/$CONTAINER_NAME-"$(date -Format "yyyy-MM-dd-HH-mm-ss")".log"
else
    VOLUME_PATH="$(pwd)/data"
    LOG_PATH="$(pwd)/logs"
    LOG_FILE="$LOG_PATH/$CONTAINER_NAME-"$(date "+%Y-%m-%d-%H-%M-%S")".log"
fi

mkdir -p "$LOG_PATH"
touch "$LOG_FILE"

echo "Building $CONTAINER_NAME..." && docker build -t "$CONTAINER_NAME" "$SCRIPT_DIR"
if [ $? -ne 0 ]; then
    echo "Failed to build container $CONTAINER_NAME"
    exit 1
fi
echo "Stopping old $CONTAINER_NAME..." && docker stop "$CONTAINER_NAME" 2>/dev/null
echo "Removing old $CONTAINER_NAME..." && docker rm "$CONTAINER_NAME" 2>/dev/null

docker run -d\
           --rm\
           --name "$CONTAINER_NAME"\
           $(test -n "$BOT_API_TOKEN" && echo "-e BOT_API_TOKEN=$BOT_API_TOKEN")\
           $(test -n "$ACCESS_ID_GROUP" && echo "-e ACCESS_ID_GROUP=$ACCESS_ID_GROUP")\
           $(test -f "$SCRIPT_DIR/.env" && echo "--env-file $SCRIPT_DIR/.env")\
           $(test -f "$SCRIPT_DIR/.env-local" && echo "--env-file $SCRIPT_DIR/.env-local")\
           -v "$VOLUME_PATH:/data"\
           -v "$LOG_FILE:/logs/logs.log"\
           "$CONTAINER_NAME:latest"

docker logs -f "$CONTAINER_NAME"
