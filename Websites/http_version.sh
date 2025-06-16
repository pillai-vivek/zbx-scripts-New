#!/bin/bash

# Function to get HTTP version
get_http_version() {
    local url=$1
    local http_version

    # Try with HTTP/2 first
    http_version=$(timeout 10 curl -sI --http2 "$url" | grep -i '^HTTP/2' | awk '{print $1}')

    if [[ -z "$http_version" ]]; then
        # If HTTP/2 is not supported, try with HTTP/1.1
        http_version=$(timeout 10 curl -sI "$url" | grep -i '^HTTP/1.1' | awk '{print $1}')
    fi

    # If still no HTTP version detected, return "Unknown"
    if [[ -z "$http_version" ]]; then
        echo "Unknown"
    else
        echo "$http_version"
    fi
}

# Usage example

get_http_version "https://$1"


