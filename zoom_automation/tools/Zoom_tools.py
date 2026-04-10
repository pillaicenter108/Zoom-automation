import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from zoom_automation.services.zoom_service import get_access_token, ZOOM_ACCOUNTS


# ─────────────────────────────────────────
#  TIMEZONE HELPER
# ─────────────────────────────────────────

PACIFIC = ZoneInfo("America/Los_Angeles")


def _to_pacific_display(utc_str: str) -> str:
    """
    Convert a Zoom UTC time string (e.g. '2026-04-11T01:30:00Z')
    to a Pacific Time display string (e.g. 'Apr 11, 2026, 6:30 PM PDT').
    Returns the original string if parsing fails.
    """
    if not utc_str:
        return utc_str
    try:
        # Zoom returns times ending in 'Z' (UTC)
        dt_utc = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        dt_pt  = dt_utc.astimezone(PACIFIC)
        # PDT vs PST automatically handled by zoneinfo
        tz_abbr = "PDT" if dt_pt.dst().seconds else "PST"
        return dt_pt.strftime(f"%b %d, %Y, %-I:%M %p {tz_abbr}")
    except Exception:
        return utc_str


# ─────────────────────────────────────────
#  LIST MEETINGS
# ─────────────────────────────────────────

def list_meetings(zoom_account: str) -> list:
    """
    List all upcoming meetings for a given Zoom account.
    - One-time meetings are returned as-is.
    - Recurring meetings are expanded: each future occurrence is returned
      as a separate entry so all instances are visible.
    """
    token      = get_access_token(zoom_account)
    host_email = ZOOM_ACCOUNTS[zoom_account]["host_email"]
    headers    = {"Authorization": f"Bearer {token}"}
    url        = f"https://api.zoom.us/v2/users/{host_email}/meetings"
    now        = datetime.now(timezone.utc)

    all_meetings: dict[str, dict] = {}

    # Fetch both upcoming (one-time) and scheduled (recurring parents)
    for meeting_type in ("upcoming", "scheduled"):
        params   = {"type": meeting_type, "page_size": 100}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            continue

        for m in response.json().get("meetings", []):
            meeting_id   = str(m.get("id", ""))
            meeting_type_num = m.get("type", 2)

            if not meeting_id or meeting_id == "0":
                continue

            # ── Recurring meeting (type 8) → expand all occurrences ──
            if meeting_type_num == 8:
                occ_url  = f"https://api.zoom.us/v2/meetings/{meeting_id}?show_previous_occurrences=false"
                occ_resp = requests.get(occ_url, headers=headers)
                if occ_resp.status_code == 200:
                    detail       = occ_resp.json()
                    occurrences  = detail.get("occurrences", [])
                    for occ in occurrences:
                        occ_start = occ.get("start_time", "")
                        # Skip past occurrences
                        try:
                            occ_dt = datetime.fromisoformat(occ_start.replace("Z", "+00:00"))
                            if occ_dt < now:
                                continue
                        except Exception:
                            pass

                        # Build a meeting entry per occurrence
                        occ_id  = f"{meeting_id}_occ_{occ.get('occurrence_id', occ_start)}"
                        entry   = {
                            "id":         meeting_id,          # parent ID (for update/delete)
                            "occurrence_id": occ.get("occurrence_id"),
                            "topic":      detail.get("topic", m.get("topic", "Untitled")),
                            "start_time": _to_pacific_display(occ_start),
                            "duration":   occ.get("duration", detail.get("duration", "N/A")),
                            "join_url":   detail.get("join_url", m.get("join_url", "N/A")),
                            "is_recurring": True,
                        }
                        if occ_id not in all_meetings:
                            all_meetings[occ_id] = entry
                else:
                    # Fallback: show parent meeting if occurrences API fails
                    start_str = m.get("start_time", "")
                    try:
                        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                        if start_dt < now:
                            continue
                    except Exception:
                        pass
                    m["start_time"] = _to_pacific_display(start_str)
                    if meeting_id not in all_meetings:
                        all_meetings[meeting_id] = m

            # ── One-time meeting (type 2) ──
            else:
                start_str = m.get("start_time", "")
                try:
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if start_dt < now:
                        continue
                except Exception:
                    pass

                m["start_time"] = _to_pacific_display(start_str)
                if meeting_id not in all_meetings:
                    all_meetings[meeting_id] = m

    # Sort by raw start time (Pacific display is human-readable; sort on UTC)
    result = list(all_meetings.values())
    return result


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