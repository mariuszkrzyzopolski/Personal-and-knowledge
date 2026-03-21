"""
Core agentic loop: reads logs via MCP tools, analyses with DSPy, submits to hub.
Human-in-the-loop gate between iterations.
"""

from __future__ import annotations

import os

import dspy
from dotenv import load_dotenv
from rich.console import Console

from .signatures import MailResearcher
from .tools import load_history, save_history, submit_findings_to_hub, getMessages, getInbox, getThread, search

load_dotenv()

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
OPENROUTER_MODEL   = os.environ["OPENROUTER_MODEL"]
MAX_ITERATIONS     = int(os.getenv("MAX_ITERATIONS", 10))

def configure_dspy() -> dspy.ReAct:
    lm = dspy.LM(
        model=OPENROUTER_MODEL,
        api_key=OPENROUTER_API_KEY,
        api_base="https://openrouter.ai/api/v1",
    )
    dspy.configure(lm=lm)
    return dspy.ReAct(
        MailResearcher,
        tools = [
            submit_findings_to_hub,
            getMessages,
            getInbox,
            getThread,
            search
        ]
    )

def run_agent_loop() -> None:
    console = Console()
    agent = configure_dspy()
    history = load_history()
    for i in range(MAX_ITERATIONS):
        instruction = console.input("[magenta]Type instruction for agent[/magenta]")
        results = agent(sterring_message=instruction, history=history)
        console.print("[red]Agent Reasoning:[/red]", results)
        history.messages.append({"User instruction": instruction, **results})
    save_history(history)
