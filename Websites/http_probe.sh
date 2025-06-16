#!/bin/bash  
# Set the URL to probe
url="$1"
# Measure the probe duration using curl
probe_duration=$(curl -o /dev/null -s -w '%{time_total}' "$url")
# Convert the probe duration from seconds to milliseconds
probe_duration_ms=$(echo "scale=0; $probe_duration * 1000" | bc)
# Print the probe duration in milliseconds 
echo "$probe_duration_ms"
