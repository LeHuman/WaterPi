#!/bin/bash

# Arguments
PIPE_PATH=$1
TIMEOUT=$2
FULL_PATH_TO_SCRIPT="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIRECTORY="$(dirname "$FULL_PATH_TO_SCRIPT")"
COMMAND_TO_RUN="$SCRIPT_DIRECTORY/kill.sh"

echo_w() {
    echo "[Watchdog] $*"
}

# Function to clean up resources and run the fallback command
cleanup() {
    echo_w "Executing fallback command..."
    $COMMAND_TO_RUN
    if [ -e "$PIPE_PATH" ]; then
        echo_w "Cleaning up pipe"
        rm -f "$PIPE_PATH"
    fi
    touch "./fail"
    exit 1
}

# Validate arguments
if [ -z "$PIPE_PATH" ] || [ -z "$TIMEOUT" ] || ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]]; then
    echo_w "Invalid arguments. Usage: $0 <pipe_path> <timeout_in_seconds>"
    cleanup
fi

# Handle termination signals (SIGHUP, SIGTERM, etc.)
trap cleanup SIGHUP SIGTERM SIGINT SIGABRT

# Create the named pipe
echo_w "Making Pipe $PIPE_PATH"
mkfifo "$PIPE_PATH"

# Wait for a signal through the pipe or timeout
if read -t $TIMEOUT SIGNAL <>"$PIPE_PATH"; then # NOTE: Non-portable <> used here
    if [ "$SIGNAL" = "FINISH" ]; then
        echo_w "Received graceful finish signal."
        if [ -e "$PIPE_PATH" ]; then
            echo_w "Cleaning up pipe"
            rm -f "$PIPE_PATH"
        fi
        exit 0
    fi
else
    echo_w "Error reading from pipe."
fi

# Cleanup in case of unexpected conditions
cleanup
