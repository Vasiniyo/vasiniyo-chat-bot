#!/bin/bash

#  env-file: instance .env-instance (not root .env/.env-local)
#  config.toml: mounted from instance dir, overrides the COPY'd one in image
#  data volume: instance-specific
#  log file: instance-specific
#  container name: bot-$INSTANCE

if ! command -v docker &> /dev/null; then
    echo "You should install Docker: https://docs.docker.com/get-started/get-docker"
    exit 1
fi

SCRIPT_DIR="$(dirname "$(realpath -m "$0")")"
IMAGE_NAME="vasiniyo-chat-bot"

# == Usage / Help ===============================================================

usage() {
    echo "Usage: $0 -i|--instance <name> [--test]"
    echo ""
    
    if [ -d "$SCRIPT_DIR/instances" ]; then
        local available
        available=$(ls -1 "$SCRIPT_DIR/instances" 2>/dev/null)
        if [ -n "$available" ]; then
            echo "Available instances:"
            echo "$available" | sed 's/^/  /'
        fi
    fi
    exit 1
}

# == Parse args: -i|--instance NAME, --test, --completions ======================

INSTANCE=""
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--instance)
            INSTANCE="$2"
            shift 2
            ;;
        --test)
            EXTRA_ARGS="--test"
            shift
            ;;
        --completions)
            # Completion
            cat <<'COMP'
_run_sh_completions() {
    local script_dir
    script_dir="$(dirname "$(realpath -m "${COMP_WORDS[0]}")")"
    if [[ "${COMP_WORDS[COMP_CWORD-1]}" == "-i" || "${COMP_WORDS[COMP_CWORD-1]}" == "--instance" ]]; then
        COMPREPLY=($(compgen -W "$(ls -1 "$script_dir/instances" 2>/dev/null)" -- "${COMP_WORDS[COMP_CWORD]}"))
    fi
}
complete -F _run_sh_completions ./run.sh run.sh
COMP
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

INSTANCE_DIR="$SCRIPT_DIR/instances/$INSTANCE"
if [ ! -d "$INSTANCE_DIR" ]; then
    echo "Error: instance directory not found: $INSTANCE_DIR"
    usage
fi

if [ ! -f "$INSTANCE_DIR/config.toml" ]; then
    echo "Error: missing config.toml in $INSTANCE_DIR"
    exit 1
fi

# == Per-intance settings =======================================================

CONTAINER_NAME="bot-$INSTANCE"
DATA_PATH="$INSTANCE_DIR/data"
LOG_DIR="$INSTANCE_DIR/logs"

mkdir -p "$DATA_PATH"
mkdir -p "$LOG_DIR"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OS" == "Windows_NT" ]]; then
    LOG_FILE="$LOG_DIR/$CONTAINER_NAME-$(date -Format 'yyyy-MM-dd-HH-mm-ss').log"
else
    LOG_FILE="$LOG_DIR/$CONTAINER_NAME-$(date '+%Y-%m-%d-%H-%M-%S').log"
fi

touch "$LOG_FILE"

# == Shared Image ================================================================

echo "Building $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
if [ $? -ne 0 ]; then
    echo "Failed to build image $IMAGE_NAME"
    exit 1
fi

# == Starting instance ==========================================================

echo "Stopping old $CONTAINER_NAME..." && docker stop "$CONTAINER_NAME" 2>/dev/null
echo "Removing old $CONTAINER_NAME..." && docker rm "$CONTAINER_NAME" 2>/dev/null

docker run -d \
           --rm \
           --name "$CONTAINER_NAME" \
           $(test -f "$INSTANCE_DIR/.env-instance" && echo "--env-file $INSTANCE_DIR/.env-instance") \
           -v "$INSTANCE_DIR/config.toml:/config.toml:ro" \
           -v "$DATA_PATH:/data" \
           -v "$LOG_FILE:/logs/logs.log" \
           "$IMAGE_NAME:latest" \
           sh -c "python -m src $EXTRA_ARGS 2>&1 | tee /logs/logs.log"

docker logs -f "$CONTAINER_NAME"
