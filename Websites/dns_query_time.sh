#!/bin/bash

# Function to perform DNS lookup
dns_lookup() {
    website=$1
    start_time=$(date +%s%N)  # Start timestamp in nanoseconds
    ip_addresses=$(nslookup "$website" | awk '/^Address: / { print $2 }')
    end_time=$(date +%s%N)    # End timestamp in nanoseconds
    elapsed_time=$(( (end_time - start_time) / 1000000 ))  # Calculate elapsed time in milliseconds
    echo "$elapsed_time"
}

# Main script
dns_lookup "$1"
