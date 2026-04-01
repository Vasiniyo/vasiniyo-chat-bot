#!/bin/bash

#  env-file: instance .env-instance (not root .env/.env-local)
#  config.toml: mounted from instance dir, overrides the COPY'd one in image
#  data volume: instance-specific
#  log file: instance-specific
#  container name: bot-$INSTANCE

usage() {
    cat <<EOF
Usage: $(basename "$0") --instance <name> [--runtime <local|docker>] [--test]

Options:
  -r, --runtime   runtime mode (default: docker)
  -i, --instance  instance name (required)
      --test      enable test mode
  -h, --help      display this help and exit

Examples:
  $(basename "$0") --runtime local --instance bot-example --test
  $(basename "$0") -r docker -i bot-example
EOF
    exit 1
}

SCRIPT_DIR="$(dirname "$(realpath -m "$0")")"
RUNTIME_MODE="docker"
while [[ $# -gt 0 ]]; do
    case "$1" in
        -r|--runtime)
            RUNTIME_MODE="$2"
            if [[ "$RUNTIME_MODE" != "local" && "$RUNTIME_MODE" != "docker" ]]; then
                echo "Error: invalid runtime: $RUNTIME_MODE (allowed: local, docker)"
                exit 1
            fi
            if ! command -v docker &> /dev/null ; then
                echo "You should install Docker: https://docs.docker.com/get-started/get-docker"
                exit 1
            fi
            shift 2
            ;;
        -i|--instance)
            INSTANCE="$2"
            INSTANCE_DIR="$SCRIPT_DIR/instances/$INSTANCE"
            CONFIG_PATH="$INSTANCE_DIR/config.toml"
            ENV_FILE="$INSTANCE_DIR/.env-instance"
            if [ ! -d "$INSTANCE_DIR" ]; then
                echo "Error: instance directory not found: $INSTANCE_DIR"
                available=$(ls -1 "$SCRIPT_DIR/instances" 2>/dev/null)
                if [ -n "$available" ]; then
                    echo "Available instances:"
                    echo "$available" | sed 's/^/  /'
                fi
                exit 1
            fi
            if [ ! -f "$CONFIG_PATH" ]; then
                echo "Error: missing config.toml in $INSTANCE_DIR"
                exit 1
            fi
            shift 2
            ;;
        --test)
            TEST_MODE="true"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            usage
            ;;
    esac
done

if [ -z "$INSTANCE" ]; then
    usage
fi

CONTAINER_NAME="bot-$INSTANCE"
DATA_PATH="$INSTANCE_DIR/data"
LOG_DIR="$INSTANCE_DIR/logs"
DATABASE_PATH="$INSTANCE_DIR/data/database.db"

mkdir -p "$DATA_PATH" "$LOG_DIR"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OS" == "Windows_NT" ]]; then
    LOG_FILE="$LOG_DIR/$CONTAINER_NAME-$(date -Format 'yyyy-MM-dd-HH-mm-ss').log"
else
    LOG_FILE="$LOG_DIR/$CONTAINER_NAME-$(date '+%Y-%m-%d-%H-%M-%S').log"
fi

touch "$LOG_FILE"

if [[ "$RUNTIME_MODE" == "local" ]]; then
  VENV_DIR=".venv"
  if ! command -v python3 >/dev/null 2>&1; then
      echo "Error: python3 not installed"
      exit 1
  fi
  if ! python3 -m venv --help >/dev/null 2>&1; then
      echo "Error: python3-venv not installed (Debian): sudo apt install python3-venv"
      exit 1
  fi
  if [[ ! -d "$VENV_DIR" ]]; then
      echo "Creating virtual environment..."
      python3 -m venv "$VENV_DIR"
  fi
  if [[ ! -x "$VENV_DIR/bin/pip" ]]; then
    echo "Error: pip not found in venv"
    exit 1
  fi
  python="$VENV_DIR/bin/python"
  "$python" -m pip install --upgrade pip
  "$python" -m pip install -r requirements.txt
  "$python" -m pip install -e .
  export TEST_MODE CONFIG_PATH DATABASE_PATH
  set -a
  test -f "$ENV_FILE" && source "$ENV_FILE"
  set +a
  echo
  "$python" -m vasiniyo_chat_bot 2>&1 | tee "$LOG_FILE"
  exit 0
fi

echo "Building $CONTAINER_NAME..."
docker build -t "$CONTAINER_NAME:latest" "$SCRIPT_DIR"
if [ $? -ne 0 ]; then
    echo "Failed to build image $CONTAINER_NAME"
    exit 1
fi
echo "Stopping old $CONTAINER_NAME..." && docker stop "$CONTAINER_NAME" 2>/dev/null
echo "Removing old $CONTAINER_NAME..." && docker rm "$CONTAINER_NAME" 2>/dev/null
docker run -d \
           --rm \
           --name "$CONTAINER_NAME" \
           $(test -f "$ENV_FILE" && echo "--env-file $ENV_FILE") \
           -v "$CONFIG_PATH:/config.toml:ro" \
           -v "$DATA_PATH:/data" \
           -v "$LOG_FILE:/logs/logs.log" \
           -e TEST_MODE="$TEST_MODE" \
           -e CONFIG_PATH="/config.toml" \
           -e DATABASE_PATH="/data/database.db" \
           "$CONTAINER_NAME:latest"
docker logs -f "$CONTAINER_NAME"
