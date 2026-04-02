"""
LangGraph nodes.

The chatbot node is bound to every tool discovered in zoom_automation/tools/.
Adding a new tool file there automatically makes it available here.
"""

from langchain_core.messages import AnyMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langsmith import traceable
from dotenv import load_dotenv
import os
load_dotenv()

from zoom_automation.agents.state import State
from zoom_automation.tools import tools   # auto-discovered tools

# ─────────────────────────────────────────
#  LLM + tool binding
# ─────────────────────────────────────────

llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)


# ─────────────────────────────────────────
#  Message trimmer (keeps conversation safe)
# ─────────────────────────────────────────

def _safe_trim(messages: list[AnyMessage], keep_last: int = 5) -> list[AnyMessage]:
    """
    Trim old messages while keeping the system prompt and ensuring
    ToolMessages always follow an AIMessage that has tool_calls.
    """
    if len(messages) <= keep_last + 1:
        return messages

    system = messages[0]
    tail   = messages[-keep_last:]

    # Drop any leading ToolMessages that are orphaned (no preceding tool call)
    start = 0
    for i, msg in enumerate(tail):
        if isinstance(msg, ToolMessage):
            start = i + 1
        else:
            break

    return [system] + tail[start:]


# ─────────────────────────────────────────
#  Chatbot node
# ─────────────────────────────────────────

@traceable(name="chatbot_node")
def chatbot(state: State) -> State:
    messages = state["messages"]
    messages = _safe_trim(messages)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}