#!/usr/bin/python3

import boto3
import time
import json
import os
import sys
import subprocess


class RDSLogMonitor:
    def __init__(self, region, rds_instance, access_key, secret_key, zabbix_server, zabbix_host, logs_key, poll_window_seconds):
        self.region = region
        self.rds_instance = rds_instance
        self.access_key = access_key
        self.secret_key = secret_key
        self.zabbix_server = zabbix_server
        self.zabbix_host = zabbix_host
        self.logs_key = logs_key
        self.poll_window_seconds = int(poll_window_seconds)
        self.index_file = f"/var/tmp/{self.rds_instance}_rds_index.json"

        self.logs_client = boto3.client(
            'logs',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        self.rds_client = boto3.client(
            'rds',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        self.log_group = self.get_log_group_from_instance()

    def get_log_group_from_instance(self):
        response = self.rds_client.describe_db_instances(DBInstanceIdentifier=self.rds_instance)
        arn = response['DBInstances'][0]['DBInstanceArn']
        return f"/aws/rds/instance/{self.rds_instance}/error"

    def load_last_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as f:
                return json.load(f)
        return None

    def save_last_index(self, stream, event_id):
        with open(self.index_file, "w") as f:
            json.dump({"stream": stream, "event_id": event_id}, f)

    def get_new_logs(self):
        now = int(time.time() * 1000)
        start_time = now - self.poll_window_seconds * 1000
        last_index = self.load_last_index()

        events = []
        next_token = None

        while True:
            kwargs = {
                "logGroupName": self.log_group,
                "startTime": start_time,
                "interleaved": True
            }
            if next_token:
                kwargs["nextToken"] = next_token

            resp = self.logs_client.filter_log_events(**kwargs)

            for e in resp.get("events", []):
                if last_index and e["logStreamName"] == last_index["stream"] and e["eventId"] == last_index["event_id"]:
                    continue
                events.append(e)

            next_token = resp.get("nextToken")
            if not next_token:
                break

        if events:
            last_event = events[-1]
            self.save_last_index(last_event["logStreamName"], last_event["eventId"])

        return events

    def send_logs_to_zabbix(self, logs):
        for line in logs:
            formatted = f"[{line['logStreamName']}] {line['timestamp']} {line['message'].strip()}"
            subprocess.run([
                "/usr/bin/zabbix_sender", "-z", self.zabbix_server,
                "-s", self.zabbix_host,
                "-k", self.logs_key,
                "-o", formatted
            ])

    def run(self):
        events = self.get_new_logs()
        self.send_logs_to_zabbix(events)
        return len(events)


if __name__ == "__main__":
    if len(sys.argv) != 9:
        print("Usage: script.py <region> <rds_instance> <access_key> <secret_key> <zabbix_server> <zabbix_host> <logs_key> <poll_window_seconds>")
        sys.exit(1)

    region, rds_instance, access_key, secret_key, zabbix_server, zabbix_host, logs_key, poll_window = sys.argv[1:]

    monitor = RDSLogMonitor(region, rds_instance, access_key, secret_key, zabbix_server, zabbix_host, logs_key, poll_window)
    count = monitor.run()
    print(count)


 