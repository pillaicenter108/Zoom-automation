import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

from zoom_automation.tools.tool_schema import tools
from zoom_automation.tools.tools import execute_tools

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# All tools including delete_meeting are available
SAFE_TOOLS = tools


# ─────────────────────────────────────────
#  REQUIRED FIELDS PER TOOL
# ─────────────────────────────────────────

REQUIRED_FIELDS = {
    "create_meeting": ["topic", "start_time", "duration", "zoom_account"],
    "list_meetings":  ["zoom_account"],
    "update_meeting": ["meeting_id", "zoom_account"],
    "delete_meeting": ["meeting_id", "zoom_account"],
}

FIELD_QUESTIONS = {
    "topic":       "What should the meeting be called? (topic/title)",
    "start_time":  "What date and time should it start? (e.g. March 20 at 3pm)",
    "duration":    "How long should the meeting be? (e.g. 60 minutes, 2 hours)",
    "zoom_account":"Which Zoom account should I use? (e.g. zoom 1, zoom 2, zoom 3)",
    "meeting_id":  "What is the Meeting ID you want to update?",
}


# ─────────────────────────────────────────
#  INTENT EXTRACTION  (partial is fine)
# ─────────────────────────────────────────

EXTRACT_SYSTEM_PROMPT = """You extract user intent into a JSON object.
Return ONLY raw JSON — no markdown fences, no explanation, nothing else.

Supported tools:

  create_meeting (one-time):
    {"tool": "create_meeting", "topic": "...", "start_time": "YYYY-MM-DDTHH:MM:SS", "duration": <int_minutes>, "zoom_account": "..."}

  create_meeting (recurring — weekly repeat):
    {"tool": "create_meeting", "topic": "...", "start_time": "YYYY-MM-DDTHH:MM:SS", "duration": <int_minutes>, "zoom_account": "...", "recurrence": true, "occurrences": <int>}

  list_meetings:
    {"tool": "list_meetings", "zoom_account": "..."}

  update_meeting (NEVER include recurrence or occurrences):
    {"tool": "update_meeting", "meeting_id": "...", "zoom_account": "...", "topic": "...", "start_time": "YYYY-MM-DDTHH:MM:SS", "duration": <int_minutes>}

  delete_meeting:
    {"tool": "delete_meeting", "meeting_id": "...", "zoom_account": "..."}

Rules:
- Current year is 2026. Always use 2026 when no year is mentioned.
- zoom_account: always keep a space — 'zoom1'→'zoom 1', 'zoom3'→'zoom 3'.
- duration is always an integer (minutes). Convert hours: 2 hours → 120.
- start_time must be ISO format YYYY-MM-DDTHH:MM:SS (no timezone).
- For update_meeting: include only the fields the user wants to change, plus meeting_id and zoom_account.
- IMPORTANT: If a field is not mentioned by the user, DO NOT include it in the JSON.
  Only include fields that the user has clearly provided.
- RECURRENCE DETECTION: phrases like "every week", "weekly", "next N weeks", "upcoming N weeks",
  "for N weeks" → set recurrence=true, occurrences=N.
"""

MERGE_SYSTEM_PROMPT = """You merge two JSON objects representing partial meeting info.
The first is what we already know. The second is new info from the user's latest message.
Return ONLY the merged raw JSON — no markdown, no explanation.
New values override old ones. Keep all existing fields unless overridden.
Apply the same rules: zoom_account needs a space ('zoom1'→'zoom 1'), 
duration is always an integer (minutes), start_time is YYYY-MM-DDTHH:MM:SS.
Current year is 2026.
"""


# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def normalize_zoom_account(value: str) -> str:
    """Ensure zoom account has a space: 'zoom3' → 'zoom 3'"""
    v = value.strip().lower()
    return re.sub(r'(zoom)(\d)', lambda m: m.group(1) + ' ' + m.group(2), v)


def normalize_action(action: dict) -> dict:
    """Normalize all fields in the action dict."""
    if "zoom_account" in action:
        action["zoom_account"] = normalize_zoom_account(action["zoom_account"])
    if "duration" in action:
        try:
            action["duration"] = int(action["duration"])
        except (ValueError, TypeError):
            pass
    return action


def llm_extract(messages: list) -> dict:
    """Call LLM to extract intent from a conversation."""
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=400
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"```$", "", raw).strip()
    return json.loads(raw)


def get_missing_fields(tool_name: str, action: dict) -> list:
    """Return list of required fields that are missing from action."""
    required = REQUIRED_FIELDS.get(tool_name, [])
    return [f for f in required if not action.get(f)]


def ask_for_fields(missing: list) -> str:
    """Build a friendly question asking for the first missing field."""
    field = missing[0]
    question = FIELD_QUESTIONS.get(field, f"Could you provide the {field}?")
    if len(missing) > 1:
        remaining = ", ".join(missing[1:])
        return f"{question}\n\n*(I'll also need: {remaining})*"
    return question


# ─────────────────────────────────────────
#  RESULT FORMATTER
# ─────────────────────────────────────────

def format_meeting_list(meetings: list, zoom_account: str) -> str:
    """
    Format meeting list returned by Zoom API (already filtered to upcoming by Zoom).
    Sort by start time soonest first.
    Each line uses [ID:xxxxx] marker so UI renders inline copy button.
    """
    from datetime import datetime as _dt, timezone as _tz

    if not meetings:
        return f"No upcoming meetings found in **{zoom_account.title()}**."

    # Parse and sort by start time — soonest first
    parsed = []
    for m in meetings:
        start = m.get("start_time", "")
        try:
            dt = _dt.fromisoformat(start.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_tz.utc)
        except Exception:
            dt = _dt.min.replace(tzinfo=_tz.utc)
        parsed.append((dt, m))

    parsed.sort(key=lambda x: x[0])

    lines = [f"Here are the upcoming meetings in **{zoom_account.title()}** ({len(parsed)} found):\n"]

    # Convert UTC → Pacific time for display
    try:
        from zoneinfo import ZoneInfo
        pacific = ZoneInfo("America/Los_Angeles")
    except ImportError:
        pacific = None  # fallback: show UTC if zoneinfo not available

    for dt, m in parsed:
        topic    = m.get("topic", "Untitled")
        raw_id   = str(m.get("id", "")).replace(" ", "")
        duration = m.get("duration", 0)

        # Convert to Pacific
        if pacific and dt.tzinfo is not None:
            dt_display = dt.astimezone(pacific)
            tz_label = "PT"
        else:
            dt_display = dt
            tz_label = "UTC"

        date_str = dt_display.strftime("%b %d, %Y")
        time_str = dt_display.strftime("%I:%M %p").lstrip("0")
        lines.append(f"**{topic}** — {date_str} at {time_str} {tz_label} · {duration} min · ID: [ID:{raw_id}]")

    return "\n".join(lines)


def format_result(tool_name: str, tool_result, user_input: str, zoom_account: str = "") -> str:
    # ── Meeting list: format directly, no LLM ──
    if tool_name == "list_meetings":
        meetings = tool_result if isinstance(tool_result, list) else []
        return format_meeting_list(meetings, zoom_account)

    # ── All other tools: LLM confirmation ──
    system_content = (
        "You are ZoomFlow AI. Confirm what was just done in 1-2 friendly sentences. "
        "Never mention tool names, raw JSON, or technical details."
    )

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": (
                    f"User asked: \"{user_input}\"\n"
                    f"Tool result:\n"
                    f"{json.dumps(tool_result, indent=2) if isinstance(tool_result, (dict, list)) else str(tool_result)}"
                )
            }
        ],
        max_tokens=300
    )
    return resp.choices[0].message.content or str(tool_result)


# ─────────────────────────────────────────
#  MAIN AGENT ENTRY POINT
# ─────────────────────────────────────────

def run_agent(user_input: str, history: list) -> tuple[str, bool, str | None, dict | None]:
    """
    Conversational agent that collects missing parameters across turns.

    Args:
        user_input  — latest message from the user
        history     — full chat history list of {"role": ..., "content": ..., "pending_action": ...}

    Returns:
        text_reply      (str)        — response to show the user
        is_list         (bool)       — True if this was list_meetings
        tool_name       (str | None) — which tool was called
        pending_action  (dict | None)— partial action to carry forward, None when complete
    """
    try:
        # ── Check if we have a pending (incomplete) action from a previous turn ──
        # We look for the MOST RECENT assistant message that has pending_action.
        # If it's "CLEARED" it means the flow finished — stop looking.
        pending_action = None
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                pa = msg.get("pending_action")
                if pa == "CLEARED":
                    break          # flow was completed/cancelled — no pending state
                if pa and isinstance(pa, dict):
                    pending_action = pa.copy()
                    break

        if pending_action:
            tool_name = pending_action.get("_tool")

            # ── Handle delete confirmation separately ──
            if pending_action.get("_awaiting_confirm"):
                cancel_words = ["no", "cancel", "stop", "abort", "nope"]
                confirm_words = ["yes", "confirm", "sure", "ok", "proceed", "go ahead", "yep", "yeah"]

                user_lower = user_input.strip().lower()

                if any(w in user_lower for w in cancel_words):
                    return "Cancelled. The meeting was not deleted.", False, None, "CLEARED"

                if any(w in user_lower for w in confirm_words):
                    # Execute the delete now
                    mid  = pending_action.get("meeting_id")
                    zacc = pending_action.get("zoom_account")
                    result = execute_tools("delete_meeting", {"meeting_id": mid, "zoom_account": zacc})
                    za = zacc or ""
                    reply = format_result("delete_meeting", result, user_input, zoom_account=za)
                    return reply, False, "delete_meeting", "CLEARED"

                # Not a clear yes/no — ask again
                mid  = pending_action.get("meeting_id", "")
                zacc = pending_action.get("zoom_account", "")
                return (
                    f"Please reply **yes** to delete meeting `{mid}` from **{zacc}**, or **no** to cancel.",
                    False, None, pending_action
                )

            # ── Normal pending: merge new info into existing fields ──
            existing_json = {k: v for k, v in pending_action.items() if not k.startswith("_")}

            merged = llm_extract([
                {"role": "system", "content": MERGE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Existing info: {json.dumps(existing_json)}\n"
                        f"User just said: \"{user_input}\"\n"
                        f"Merge and return the combined JSON."
                    )
                }
            ])
            action = normalize_action(merged)

        else:
            # Fresh request — extract intent from scratch using full conversation context
            conv_messages = [{"role": "system", "content": EXTRACT_SYSTEM_PROMPT}]
            for msg in history[-6:]:  # last 6 turns for context
                if msg["role"] in ("user", "assistant") and msg.get("content"):
                    conv_messages.append({"role": msg["role"], "content": msg["content"]})
            conv_messages.append({"role": "user", "content": user_input})

            extracted = llm_extract(conv_messages)
            tool_name = extracted.pop("tool", None)

            if not tool_name:
                return (
                    "I'm not sure what you'd like to do. You can ask me to:\n"
                    "- **Create** a meeting\n"
                    "- **List** meetings in a zoom account\n"
                    "- **Update** an existing meeting",
                    False, None, None
                )

            action = normalize_action(extracted)

        # ── Check for missing required fields ──
        missing = get_missing_fields(tool_name, action)

        if missing:
            # Store partial state and ask for next missing field
            pending = {"_tool": tool_name, **action}
            question = ask_for_fields(missing)
            return question, False, None, pending

        # ── All fields collected — validate and execute ──

        # Recurrence handling for create_meeting
        if tool_name == "create_meeting":
            if action.get("recurrence") is True:
                action["recurrence"] = True
            else:
                action.pop("recurrence", None)
                action.pop("occurrences", None)

        # Recurrence not supported for update_meeting
        elif tool_name == "update_meeting":
            has_recurrence = action.pop("recurrence", None)
            action.pop("occurrences", None)
            if has_recurrence:
                return (
                    "⚠️ Recurring scheduling isn't supported for existing meetings. "
                    "I can only update the **time, topic, or duration**. "
                    "To create a new recurring series, just ask me to create a new meeting.",
                    False, None, None
                )

            # update_meeting needs at least one field to change besides meeting_id and zoom_account
            update_fields = {k: v for k, v in action.items()
                             if k not in ("meeting_id", "zoom_account")}
            if not update_fields:
                return (
                    "What would you like to change? Please tell me the new **topic**, **time**, or **duration**.",
                    False, None, None
                )

        # ── Delete: ask for confirmation if not already confirmed ──
        if tool_name == "delete_meeting":
            # Check if user confirmed in this message
            confirm_words = ["yes", "confirm", "sure", "delete it", "go ahead", "ok", "proceed"]
            user_confirmed = any(w in user_input.lower() for w in confirm_words)

            if not user_confirmed:
                mid = action.get("meeting_id", "")
                zacc = action.get("zoom_account", "")
                # Store pending with confirmation flag
                pending = {"_tool": "delete_meeting", "meeting_id": mid, "zoom_account": zacc, "_awaiting_confirm": True}
                return (
                    f"⚠️ Are you sure you want to **permanently delete** meeting `{mid}` from **{zacc}**? This cannot be undone.\n\nReply **yes** to confirm or **no** to cancel.",
                    False, None, pending
                )

            # Check if user said no
            cancel_words = ["no", "cancel", "stop", "don't", "abort"]
            if any(w in user_input.lower() for w in cancel_words) and not any(w in user_input.lower() for w in ["yes", "confirm"]):
                return "Cancelled. The meeting was not deleted.", False, None, None

        # Execute the tool
        result = execute_tools(tool_name, action)

        # Format result as natural language
        za = action.get("zoom_account", "")
        reply = format_result(tool_name, result, user_input, zoom_account=za)

        # Return with no pending action (conversation complete)
        return reply, (tool_name == "list_meetings"), tool_name, "CLEARED"

    except json.JSONDecodeError as e:
        return (
            f"I had trouble understanding that. Could you rephrase? (Details: {e})",
            False, None, None
        )
    except Exception as e:
        return (
            f"⚠️ Something went wrong: {e}",
            False, None, None
        )