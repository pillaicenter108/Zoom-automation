"""
Auto-discovers and exports all LangChain @tool functions from every .py file
in this folder (except __init__.py itself).

To add new tools: just create a new .py file here with @tool decorated functions.
They will be picked up automatically — no registration needed.
"""

import importlib
import pkgutil
from pathlib import Path
from langchain_core.tools import BaseTool

_tools: list[BaseTool] = []

_package_dir = Path(__file__).parent

for module_info in pkgutil.iter_modules([str(_package_dir)]):
    module = importlib.import_module(f".{module_info.name}", package=__name__)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        # LangChain @tool produces a StructuredTool which is a BaseTool
        if isinstance(attr, BaseTool):
            _tools.append(attr)

# Deduplicate by name (in case of re-imports)
seen = set()
tools: list[BaseTool] = []
for t in _tools:
    if t.name not in seen:
        seen.add(t.name)
        tools.append(t)

__all__ = ["tools"]