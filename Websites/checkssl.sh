#!/bin/bash

# Function to extract domain from URL
get_domain() {
    url="$1"
    domain=$(echo "$url" | sed -e 's#^https\?://##' -e 's#/$##' | awk -F[/:] '{print $1}')
    echo "$domain"
}

# Extracting the domain from the URL
domain=$(get_domain "$1")

# Check if domain is empty (indicating invalid URL)
if [ -z "$domain" ]; then
    echo "Error: Invalid URL."
    exit 1
fi

# Retrieving SSL certificate end date
data=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -enddate | sed -e 's#notAfter=##')

# Checking if data is empty (indicating an error)
if [ -z "$data" ]; then
    echo "Error: Unable to retrieve SSL certificate information."
    exit 1
fi

# Converting end date to seconds since epoch
ssldate=$(date -d "$data" '+%s')
nowdate=$(date '+%s')

# Calculating the difference in days
diff=$((($ssldate-$nowdate)/86400))

echo "$diff"
