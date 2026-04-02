"""
LangGraph graph definition.

Wires the chatbot node ↔ tools node in a standard ReAct loop.
Tools are auto-loaded from zoom_automation/tools/.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

from zoom_automation.agents.state import State
from zoom_automation.agents.nodes import chatbot
from zoom_automation.tools import tools   # auto-discovered tools

# ─────────────────────────────────────────
#  Build graph
# ─────────────────────────────────────────

builder = StateGraph(State)

builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")

graph = builder.compile()

# Wrap graph.invoke so the full run appears as one trace in LangSmith
graph.invoke = traceable(name="zoomflow_agent")(graph.invoke)