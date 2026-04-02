from zoom_automation.services.zoom_service import create_meeting
from zoom_automation.tools.Zoom_tools import list_meetings, update_meeting, delete_meeting
from datetime import datetime


def fix_year(start_time):
    """Fix year to current year while supporting timezone offsets."""
    dt = datetime.fromisoformat(start_time)
    current_year = datetime.now().year
    dt = dt.replace(year=current_year)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def execute_tools(function_name, args):

    if function_name == "create_meeting":
        zoom_account = args["zoom_account"]
        start_time_fixed = fix_year(args["start_time"])
        recurrence = args.get("recurrence", False)

        if recurrence:
            recurrence_type = "weekly"
            repeat_interval = 1
            occurrences = args.get("occurrences")
        else:
            recurrence_type = None
            repeat_interval = None
            occurrences = None

        meeting = create_meeting(
            args["topic"],
            start_time_fixed,
            args["duration"],
            zoom_account,
            recurrence_type,
            repeat_interval,
            occurrences
        )

        if meeting is None:
            return "Meeting creation failed."
        return f"Meeting '{args['topic']}' created successfully."

    elif function_name == "list_meetings":
        zoom_account = args["zoom_account"]
        return list_meetings(zoom_account)

    elif function_name == "update_meeting":
        zoom_account = args["zoom_account"]
        cleaned_args = {k: v for k, v in args.items() if v is not None}
        cleaned_args["zoom_account"] = zoom_account
        if "start_time" in cleaned_args:
            cleaned_args["start_time"] = fix_year(cleaned_args["start_time"])
        return update_meeting(**cleaned_args)

    elif function_name == "delete_meeting":
        meeting_id = args["meeting_id"]
        zoom_account = args["zoom_account"]
        return delete_meeting(meeting_id=meeting_id, zoom_account=zoom_account)

    return {"error": "Tool not found"}