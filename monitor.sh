#!/bin/bash

# Ensure the script exits when the terminal closes or an error occurs
trap 'kill $!; exit' SIGINT SIGTERM SIGHUP SIGABRT EXIT

# Run the program in the background
./go2rtc_linux_arm64 &

echo ""
echo "http://$(hostname):1984/stream.html?src=usbcam&mode=mse"
echo ""

# Wait for the background process to finish
wait $!
