import requests
from datetime import datetime, timezone
from zoom_automation.services.zoom_service import get_access_token, ZOOM_ACCOUNTS


# ─────────────────────────────────────────
#  LIST MEETINGS
# ─────────────────────────────────────────

def list_meetings(zoom_account: str) -> list:
    """List all upcoming meetings for a given Zoom account."""
    token = get_access_token(zoom_account)
    host_email = ZOOM_ACCOUNTS[zoom_account]["host_email"]

    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.zoom.us/v2/users/{host_email}/meetings"
    now = datetime.now(timezone.utc)

    all_meetings: dict[str, dict] = {}

    # 'upcoming' — one-time scheduled meetings
    # 'scheduled' — catches recurring meetings with proper parent IDs
    for meeting_type in ("upcoming", "scheduled"):
        params = {"type": meeting_type, "page_size": 100}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            continue
        for m in response.json().get("meetings", []):
            # Filter to future meetings only
            start_time_str = m.get("start_time", "")
            if start_time_str:
                try:
                    start_dt = datetime.fromisoformat(
                        start_time_str.replace("Z", "+00:00")
                    )
                    if start_dt < now:
                        continue  # skip past meetings
                except ValueError:
                    pass

            meeting_id = str(m.get("id", ""))
            if meeting_id and meeting_id != "0" and meeting_id not in all_meetings:
                all_meetings[meeting_id] = m

    return list(all_meetings.values())


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
