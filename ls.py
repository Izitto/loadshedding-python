import json
import threading
from time import sleep
import requests
from app import app
from datetime import datetime, timedelta
from modules.database import populate_record, get_record_by_zone, get_all_records, wipe_table
import yaml

# Global variables for YAML and CSV URLs
yaml_url = "https://github.com/beyarkay/eskom-calendar/raw/main/manually_specified.yaml"
csv_url = "https://github.com/beyarkay/eskom-calendar/releases/download/latest/machine_friendly.csv"

# Global variables to store YAML and CSV contents
yaml_content = None
csv_content = None
time_now = None


def download_yaml_and_csv():
    global yaml_content, csv_content

    # Download YAML content
    response = requests.get(yaml_url)
    if response.status_code == 200:
        yaml_content = yaml.safe_load(response.text)
    else:
        raise ValueError(f"Failed to download YAML. Status code: {response.status_code}")

    # Download CSV content
    response = requests.get(csv_url)
    if response.status_code == 200:
        csv_content = response.text
    else:
        raise ValueError(f"Failed to download CSV. Status code: {response.status_code}")

def current_time():
    # Get the current time in South African standard time
    current = datetime.now()
    return current.strftime("%Y-%m-%dT%H:%M:%S+02:00")
def get_ls_schedule(zone_name):
    global csv_content

    if csv_content is None:
        raise ValueError("CSV content not available. Download the content first.")

    lines = csv_content.strip().split("\n")

    # Search for rows matching the area name
    ls_schedule_list = []
    for line in lines:
        columns = line.split(",")
        if columns[0] == zone_name:
            # Check if the time difference is more than 30 minutes
            start_time = datetime.strptime(columns[1], "%Y-%m-%dT%H:%M:%S+02:00")
            end_time = datetime.strptime(columns[2], "%Y-%m-%dT%H:%M:%S+02:00")
            time_diff = end_time - start_time
            if time_diff > timedelta(minutes=30):
                ls_schedule_list.append(columns[:4] + [columns[4]])

    return ls_schedule_list
def get_next_off_time(list, time_now):
    current = time_now
    
    # Find the first record with a starting time later than the current time
    for record in list:
        if record[1] > current:
            return record[1]

    
    return None
def get_next_off_day(list, time_now):
    current = datetime.strptime(time_now, "%Y-%m-%dT%H:%M:%S+02:00").date()

    # Find the first record with a starting time later than the current time
    for record in list:
        start_time = datetime.strptime(record[1], "%Y-%m-%dT%H:%M:%S+02:00").date()
        if record[1] > current_time():
            time_diff = start_time - current
            return time_diff.days

    return 0
def get_next_on_time(list, time_now):
    current = time_now
    
    # Find the first record with an ending time later than the current time
    for record in list:
        if record[2] > current:
            return record[2]
    
    return None
def get_power_status(list, time_now):
    current = time_now
    
    # Check if the current time is between any schedule's starting and ending time
    for record in list:
        if record[1] <= current <= record[2]:
            return 0
    
    return 1
def get_current_stage(list, time_now):
    # Fetch the YAML data from the provided URL
    global yaml_content
    if yaml_content is None:
        raise ValueError("YAML content not available. Download the content first.")
    current = time_now
    for change in yaml_content["changes"]:
        start_time = str(change["start"])
        finish_time = str(change["finsh"])
        
        source = change["source"].replace('"', "")
        # Check if the current time is within the start and finish times
        check_source = list[0][4].replace('"', "")
        if source == check_source:
            if start_time < current < finish_time:
                return int(change["stage"])

    return 0



