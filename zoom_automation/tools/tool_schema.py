tools = [
    {
        "type": "function",
        "function": {
            "name": "create_meeting",
            "description": "Create a Zoom meeting. If recurrence is true it will repeat weekly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic of the meeting"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Meeting start time in ISO format YYYY-MM-DDTHH:MM:SS"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duration in minutes"
                    },
                    "zoom_account": {
                        "type": "string",
                        "description": "Zoom account to use (zoom 1, zoom 2, zoom 3)"
                    },
                    "recurrence": {
                        "type": "boolean",
                        "description": "If true, meeting repeats weekly"
                    },
                    "occurrences": {
                        "type": "integer",
                        "description": "Number of weeks the meeting repeats"
                    }
                },
                "required": ["topic", "start_time", "duration", "zoom_account"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_meetings",
            "description": "List Zoom meetings for a Zoom account",
            "parameters": {
                "type": "object",
                "properties": {
                    "zoom_account": {
                        "type": "string",
                        "description": "Zoom account (zoom 1, zoom 2, zoom 3)"
                    }
                },
                "required": ["zoom_account"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_meeting",
            "description": "Update an existing Zoom meeting's topic, time, or duration",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "Zoom meeting ID"
                    },
                    "zoom_account": {
                        "type": "string",
                        "description": "Zoom account the meeting belongs to"
                    },
                    "topic": {
                        "type": ["string", "null"],
                        "description": "New meeting topic"
                    },
                    "start_time": {
                        "type": ["string", "null"],
                        "description": "New start time in ISO format YYYY-MM-DDTHH:MM:SS"
                    },
                    "duration": {
                        "type": ["integer", "null"],
                        "description": "New duration in minutes"
                    }
                },
                "required": ["meeting_id", "zoom_account"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_meeting",
            "description": "Permanently delete a Zoom meeting by its meeting ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "The Zoom meeting ID to delete"
                    },
                    "zoom_account": {
                        "type": "string",
                        "description": "Zoom account the meeting belongs to"
                    }
                },
                "required": ["meeting_id", "zoom_account"]
            }
        }
    }
]