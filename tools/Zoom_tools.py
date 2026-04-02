import requests
from zoom_automation.services.zoom_service import get_access_token, ZOOM_ACCOUNTS


# ─────────────────────────────────────────
#  LIST MEETINGS
# ─────────────────────────────────────────

def list_meetings(zoom_account: str) -> list:
    """List all scheduled meetings for a given Zoom account."""
    token = get_access_token(zoom_account)
    host_email = ZOOM_ACCOUNTS[zoom_account]["host_email"]

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.zoom.us/v2/users/{host_email}/meetings"
    params = {"type": "upcoming", "page_size": 100}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []
    return response.json().get("meetings", [])


# ─────────────────────────────────────────
#  UPDATE MEETING
# ─────────────────────────────────────────

def update_meeting(meeting_id: str,
                   zoom_account: str,
                   topic: str = None,
                   start_time: str = None,
                   duration: int = None) -> str:
    """Update an existing Zoom meeting's topic, start time, or duration."""
    token = get_access_token(zoom_account)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {}
    if topic:
        payload["topic"] = topic
    if start_time:
        payload["start_time"] = start_time
        payload["timezone"] = "America/Los_Angeles"
    if duration:
        payload["duration"] = int(duration)

    if not payload:
        return "No fields to update were provided."

    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    response = requests.patch(url, json=payload, headers=headers)

    if response.status_code == 204:
        return f"Meeting {meeting_id} updated successfully."
    return f"Failed to update meeting. Error: {response.text}"


# ─────────────────────────────────────────
#  DELETE MEETING
# ─────────────────────────────────────────

def delete_meeting(meeting_id: str, zoom_account: str) -> str:
    """Permanently delete a Zoom meeting by its ID."""
    token = get_access_token(zoom_account)

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        return f"Meeting {meeting_id} has been successfully deleted."
    if response.status_code == 404:
        return f"Meeting {meeting_id} was not found. It may have already been deleted."
    return f"Failed to delete meeting {meeting_id}. Error: {response.text}"