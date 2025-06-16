import requests
from azure.identity import ClientSecretCredential
import sys
import os
import subprocess

# Fetch values from command-line arguments
try:
    TENANT_ID = sys.argv[1]
    CLIENT_ID = sys.argv[2]
    CLIENT_SECRET = sys.argv[3]
    APP_SERVICE_NAME = sys.argv[4]
    WEBJOB_NAME = sys.argv[5]
    DOMAIN_URL = sys.argv[6]
    WEBJOB_TYPE = sys.argv[7]  # continuous or triggered
    HOSTNAME = sys.argv[8]
    ZABBIX_KEY = f"log[{WEBJOB_NAME}]"  # Key to use in Zabbix for sending log lines
except IndexError:
    print("0")  # Print 0 if arguments are missing
    sys.exit(1)

# Construct the log URL using provided values
LOG_URL = f"https://{DOMAIN_URL}/vfs/data/jobs/{WEBJOB_TYPE}/{WEBJOB_NAME}/job_log.txt"

# Position file to track the last read position
POSITION_FILE = f'/tmp/{WEBJOB_NAME}_position.file'
LOG_FILE = f'/tmp/{WEBJOB_NAME}_logs.txt'

# Initialize position file if it doesn't exist
if not os.path.exists(POSITION_FILE):
    with open(POSITION_FILE, 'w') as f:
        f.write('0')

# Authenticate using the service principal
try:
    credential = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    token = credential.get_token("https://management.azure.com/.default").token

    # Get the logs with the Bearer token
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(LOG_URL, headers=headers)

    if response.status_code == 200:
        # Save logs to a file
        with open(LOG_FILE, 'w') as f:
            f.write(response.text)

        # Read the last position from the position file
        with open(POSITION_FILE, 'r') as f:
            last_position = int(f.read().strip())

        # Get the current size of the log file
        current_size = os.path.getsize(LOG_FILE)

        # If new lines were added, read and process them
        if current_size > last_position:
            with open(LOG_FILE, 'r') as f:
                f.seek(last_position)
                new_lines = f.read()

            # Send new lines to Zabbix using zabbix_sender without printing output
            for line in new_lines.splitlines():
                subprocess.run(
                    ['zabbix_sender', '-z', '127.0.0.1', '-s', HOSTNAME, '-k', ZABBIX_KEY, '-o', line],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            # Update the last position
            with open(POSITION_FILE, 'w') as f:
                f.write(str(current_size))

        print("1")  # Successful execution
    else:
        print("0")  # Failed to fetch logs
        sys.exit(1)

except Exception as e:
    print("0")  # General failure
    sys.exit(1)
