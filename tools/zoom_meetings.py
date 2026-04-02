"""
Zoom meeting tools for LangGraph.

Wraps the real Zoom API calls from:
  - zoom_automation/services/zoom_service.py  → create_meeting
  - zoom_automation/tools/Zoom_tools.py       → list, update, delete

Uses LangChain @tool decorators so LangGraph can auto-generate schemas
from type hints + docstrings.
"""

from datetime import datetime
from langchain_core.tools import tool
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

from zoom_automation.services.zoom_service import create_meeting as _create_meeting
from zoom_automation.tools.Zoom_tools import (
    list_meetings as _list_meetings,
    update_meeting as _update_meeting,
    delete_meeting as _delete_meeting,
)


# ─────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────

def _fix_year(start_time: str) -> str:
    """Force the year to the current year in an ISO datetime string."""
    dt = datetime.fromisoformat(start_time)
    dt = dt.replace(year=datetime.now().year)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


# ─────────────────────────────────────────
#  TOOLS
# ─────────────────────────────────────────

@tool
@traceable(name="tool_create_meeting")
def create_meeting(
    topic: str,
    start_time: str,
    duration: int,
    zoom_account: str,
    recurrence: bool = False,
    occurrences: int | None = None,
) -> str:
    """
    Create a new Zoom meeting. Supports one-time or weekly recurring meetings.

    Args:
        topic:        Title of the meeting.
        start_time:   Start time in ISO format YYYY-MM-DDTHH:MM:SS.
        duration:     Duration in minutes (integer).
        zoom_account: Which account to use — 'zoom 1', 'zoom 2', or 'zoom 3'.
        recurrence:   Set True to repeat weekly (default False).
        occurrences:  Number of weekly repeats (only when recurrence=True).

    Returns:
        Confirmation message or error string.
    """
    start_time = _fix_year(start_time)

    recurrence_type = "weekly" if recurrence else None
    repeat_interval = 1        if recurrence else None
    occ             = occurrences if recurrence else None

    meeting = _create_meeting(
        topic,
        start_time,
        duration,
        zoom_account,
        recurrence_type,
        repeat_interval,
        occ,
    )

    if meeting is None:
        return "Meeting creation failed."
    return f"Meeting '{topic}' created successfully."


@tool
@traceable(name="tool_list_meetings")
def list_meetings(zoom_account: str) -> str:
    """
    List all upcoming Zoom meetings for a given account.

    Args:
        zoom_account: Which account to query — 'zoom 1', 'zoom 2', or 'zoom 3'.

    Returns:
        Formatted string listing each meeting with Meeting ID, topic,
        start time, duration, and join URL.
        Always display the Meeting ID — it is required for update or delete.
    """
    meetings = _list_meetings(zoom_account)

    if not meetings:
        return f"No upcoming meetings found in {zoom_account}."

    lines = [f"Upcoming meetings in {zoom_account} ({len(meetings)} found):\n"]
    for m in meetings:
        lines.append(
            f"• {m.get('topic', 'Untitled')}\n"
            f"  Meeting ID : {m.get('id', 'N/A')}\n"
            f"  Start      : {m.get('start_time', 'N/A')}\n"
            f"  Duration   : {m.get('duration', 'N/A')} minutes\n"
            f"  Join URL   : {m.get('join_url', 'N/A')}\n"
        )
    return "\n".join(lines)


@tool
@traceable(name="tool_update_meeting")
def update_meeting(
    meeting_id: str,
    zoom_account: str,
    topic: str | None = None,
    start_time: str | None = None,
    duration: int | None = None,
) -> str:
    """
    Update an existing Zoom meeting's topic, start time, or duration.

    Args:
        meeting_id:   The Zoom meeting ID to update.
        zoom_account: Account the meeting belongs to — 'zoom 1', 'zoom 2', or 'zoom 3'.
        topic:        New meeting title (optional).
        start_time:   New start time ISO format YYYY-MM-DDTHH:MM:SS (optional).
        duration:     New duration in minutes (optional).

    Note: Provide at least one of topic, start_time, or duration.

    Returns:
        Success or error message.
    """
    if start_time:
        start_time = _fix_year(start_time)

    return _update_meeting(
        meeting_id=meeting_id,
        zoom_account=zoom_account,
        topic=topic,
        start_time=start_time,
        duration=duration,
    )


@tool
@traceable(name="tool_delete_meeting")
def delete_meeting(meeting_id: str, zoom_account: str) -> str:
    """
    Permanently delete a Zoom meeting.

    Args:
        meeting_id:   The Zoom meeting ID to delete.
        zoom_account: Account the meeting belongs to — 'zoom 1', 'zoom 2', or 'zoom 3'.

    Returns:
        Success or error message.
    """
    return _delete_meeting(meeting_id=meeting_id, zoom_account=zoom_account)