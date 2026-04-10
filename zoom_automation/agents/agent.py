"""
agent.py — LangGraph entry point for the Zoom Automation agent.

Replaces the old manual Groq loop with a proper LangGraph ReAct agent.
All tool discovery, routing, and memory management is handled by the graph.

Usage:
    python -m zoom_automation.agent
    # or
    python agent.py
"""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from zoom_automation.agents.graph import graph
from zoom_automation.agents.state import State

# ─────────────────────────────────────────
#  System prompt
# ─────────────────────────────────────────

SYSTEM_PROMPT = """
You are ZoomFlow AI, a helpful assistant that manages Zoom meetings.

You have access to tools that can create, list, update, and delete Zoom meetings
across multiple Zoom accounts (zoom 1, zoom 2, zoom 3).

Rules:
1. Read the user's request carefully and identify what they want to do.
2. Choose the right tool for the task.
3. Only call a tool when ALL required parameters are available.
4. If a required parameter is missing, ask the user for it — never guess.
   Required parameters per tool:
   - create_meeting: topic, start_time, duration, zoom_account
   - list_meetings:  zoom_account
   - update_meeting: meeting_id, zoom_account (+ at least one of topic/start_time/duration)
   - delete_meeting: meeting_id, zoom_account
5. zoom_account must always include a space: 'zoom 1', 'zoom 2', 'zoom 3'.
   If the user says 'zoom1' normalize it to 'zoom 1'.
6. For delete requests, always confirm with the user before calling the tool.
7. When a tool returns a result, present it clearly. For meeting lists, ALWAYS
   show the Meeting ID for every meeting — it is needed for updates and deletes.
8. If no tool is needed, answer directly.
9. For multiple actions, handle them one at a time in order.

Current year is 2026. Times with no year given should default to 2026.
Always convert duration to integer minutes (e.g. '2 hours' → 120).
"""

# ─────────────────────────────────────────
#  CLI loop
# ─────────────────────────────────────────

def main() -> None:
    memory: State | None = None

    print("ZoomFlow AI — type 'quit' or 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        # Build or extend conversation state
        if memory is None:
            memory = State(
                messages=[
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_input),
                ]
            )
        else:
            memory["messages"].append(HumanMessage(content=user_input))

        # Run through LangGraph
        memory = graph.invoke(memory)

        # Extract the latest non-empty AI text reply
        reply = ""
        for msg in reversed(memory["messages"]):
            if (
                isinstance(msg, AIMessage)
                and isinstance(msg.content, str)
                and msg.content.strip()
            ):
                reply = msg.content.strip()
                break

        print(f"\nAssistant: {reply or '(no text response)'}\n")


if __name__ == "__main__":
    main()