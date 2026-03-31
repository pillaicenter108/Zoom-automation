import requests
import base64
import os
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ---------------- ZOOM ACCOUNT CONFIG ----------------

ZOOM_ACCOUNTS = {
    "zoom 1": {
        "account_id": os.getenv("ZOOM1_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM1_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM1_CLIENT_SECRET"),
        "host_email": os.getenv("ZOOM1_HOST_EMAIL")
    },
    "zoom 2": {
        "account_id": os.getenv("ZOOM2_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM2_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM2_CLIENT_SECRET"),
        "host_email": os.getenv("ZOOM2_HOST_EMAIL")
    },
    "zoom 3": {
        "account_id": os.getenv("ZOOM3_ACCOUNT_ID"),
        "client_id": os.getenv("ZOOM3_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM3_CLIENT_SECRET"),
        "host_email": os.getenv("ZOOM3_HOST_EMAIL")
    },
    # "zoom4": {
    #     "account_id": os.getenv("ZOOM4_ACCOUNT_ID"),
    #     "client_id": os.getenv("ZOOM4_CLIENT_ID"),
    #     "client_secret": os.getenv("ZOOM4_CLIENT_SECRET"),
    #     "host_email": os.getenv("ZOOM4_HOST_EMAIL")
    # }
}


# ---------------- ACCESS TOKEN ----------------

def get_access_token(zoom_account):

    creds = ZOOM_ACCOUNTS.get(zoom_account)

    if not creds:
        raise Exception(f"Invalid Zoom account: {zoom_account}")

    account_id = creds["account_id"]
    client_id = creds["client_id"]
    client_secret = creds["client_secret"]

    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"

    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode()).decode()

    headers = {"Authorization": f"Basic {encoded}"}

    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Token Error: {response.text}")

    return response.json()["access_token"]


# ---------------- VALIDATE USER ----------------

def validate_user(user_email, token):

    headers = {"Authorization": f"Bearer {token}"}

    url = f"https://api.zoom.us/v2/users/{user_email}"

    response = requests.get(url, headers=headers)

    return response.status_code == 200


# ---------------- PASSCODE ----------------

def generate_passcode():
    return str(random.randint(100000, 999999))


# ---------------- CREATE MEETING ----------------

def create_meeting(topic, start_time_pacific, duration,
                   zoom_account,
                   recurrence_type=None,
                   repeat_interval=None,
                   occurrences=None):

    token = get_access_token(zoom_account)

    host_email = ZOOM_ACCOUNTS[zoom_account]["host_email"]

    start_dt = datetime.fromisoformat(start_time_pacific)

    current_year = datetime.now().year

    if start_dt.year != current_year:
        start_dt = start_dt.replace(year=current_year)

    start_time_pacific = start_dt.isoformat()

    meeting_data = {
        "topic": topic,
        "type": 2,
        "start_time": start_time_pacific,
        "timezone": "America/Los_Angeles",
        "duration": int(duration),
        "password": generate_passcode(),
        "settings": {
            "waiting_room": True,
            "join_before_host": False
        }
    }

    # ---------------- WEEKLY RECURRENCE ----------------

    if recurrence_type == "weekly":

        dt_obj = datetime.strptime(start_time_pacific, "%Y-%m-%dT%H:%M:%S")

        python_day = dt_obj.weekday()

        zoom_day_map = {
            0: 2,
            1: 3,
            2: 4,
            3: 5,
            4: 6,
            5: 7,
            6: 1
        }

        zoom_day = zoom_day_map[python_day]

        meeting_data["type"] = 8

        meeting_data["recurrence"] = {
            "type": 2,
            "repeat_interval": 1,
            "weekly_days": str(zoom_day),
            "end_times": int(occurrences or 1)
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"https://api.zoom.us/v2/users/{host_email}/meetings"

    response = requests.post(url, json=meeting_data, headers=headers)

    if response.status_code != 201:
        print("Zoom Error:", response.text)
        return None

    meeting = response.json()

    meeting["generated_passcode"] = meeting_data["password"]

    return meeting