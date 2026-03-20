"""
Core agentic loop: reads logs via MCP tools, analyses with DSPy, submits to hub.
Human-in-the-loop gate between iterations.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import dspy
import requests
import tiktoken
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from .signatures import AnalyzeLogs, EvaluateHubResponse

load_dotenv()
console = Console()
_enc = tiktoken.get_encoding("cl100k_base")

# ── config from .env ──────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "openrouter/anthropic/claude-3.5-sonnet")
HUB_API_KEY        = os.environ["HUB_API_KEY"]
HUB_URL            = os.getenv("HUB_URL", "https://hub.ag3nts.org/verify")
HUB_TASK           = os.getenv("HUB_TASK", "failure")
LOG_FILE_PATH      = os.getenv("LOG_FILE_PATH", "failure.log")
TOKEN_BUDGET       = int(os.getenv("TOKEN_BUDGET", "1500"))
HISTORY_PATH       = Path("session_history.json")
MCP_SERVER_PATH    = Path(__file__).parent / "mcp_server.py"

# ── DSPy / OpenRouter setup ───────────────────────────────────────────────────

def configure_dspy() -> None:
    lm = dspy.LM(
        model=OPENROUTER_MODEL,
        api_key=OPENROUTER_API_KEY,
        api_base="https://openrouter.ai/api/v1",
        max_tokens=4096,
    )
    dspy.configure(lm=lm)


# ── MCP client (subprocess, stdio transport) ─────────────────────────────────

class MCPClient:
    """Minimal synchronous MCP client over stdio."""

    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._req_id = 0

    def start(self) -> None:
        self._proc = subprocess.Popen(
            [sys.executable, str(MCP_SERVER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # read the server-ready notification (MCP sends an initial handshake)
        self._send({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05",
                               "capabilities": {},
                               "clientInfo": {"name": "log-analyzer", "version": "0.1"}}})
        self._recv()  # consume initialize response
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            self._proc = None

    def _send(self, obj: dict) -> None:
        assert self._proc and self._proc.stdin
        self._proc.stdin.write(json.dumps(obj) + "\n")
        self._proc.stdin.flush()

    def _recv(self) -> dict:
        assert self._proc and self._proc.stdout
        line = self._proc.stdout.readline()
        return json.loads(line)

    def call(self, tool: str, arguments: dict) -> Any:
        self._req_id += 1
        self._send({
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        })
        resp = self._recv()
        if "error" in resp:
            raise RuntimeError(f"MCP error calling {tool}: {resp['error']}")
        content = resp["result"]["content"]
        # FastMCP returns list of {type, text} blocks
        text = "".join(block["text"] for block in content if block.get("type") == "text")
        return json.loads(text)


# ── session history ───────────────────────────────────────────────────────────

def load_history() -> list[dict]:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return []


def save_history(history: list[dict]) -> None:
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False))


def append_iteration(
    history: list[dict],
    iteration: int,
    submitted_logs: str,
    hub_response: dict,
    human_notes: str,
) -> None:
    history.append({
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "submitted_logs": submitted_logs,
        "hub_response": hub_response,
        "human_notes": human_notes,
    })
    save_history(history)


# ── hub submission ────────────────────────────────────────────────────────────

def submit_to_hub(logs_string: str) -> dict:
    payload = {
        "apikey": HUB_API_KEY,
        "task": HUB_TASK,
        "answer": {"logs": logs_string},
    }
    console.print("\n[bold cyan]→ Submitting to hub…[/bold cyan]")
    console.print(Syntax(json.dumps(payload, indent=2, ensure_ascii=False),
                         "json", theme="monokai", line_numbers=False))
    try:
        r = requests.post(HUB_URL, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}


# ── read ALL log lines via MCP (handles >2100 rows with pagination) ───────────

def read_all_lines(mcp: MCPClient) -> list[str]:
    all_lines: list[str] = []
    start = 0
    page_size = 600

    with console.status("[bold green]Reading log file…"):
        while True:
            result = mcp.call("read_log_file", {
                "path": LOG_FILE_PATH,
                "start_line": start,
                "max_lines": page_size,
            })
            if "error" in result:
                console.print(f"[red]{result['error']}[/red]")
                break
            all_lines.extend(result["lines"])
            if not result["has_more"]:
                break
            start = result["end_line"] + 1

    console.print(f"[green]✓ Read {len(all_lines)} lines from {LOG_FILE_PATH}[/green]")
    return all_lines


# ── one full agent iteration ──────────────────────────────────────────────────

def run_iteration(
    mcp: MCPClient,
    iteration: int,
    history: list[dict],
    all_lines: list[str],
) -> tuple[str, dict]:
    """
    Returns (submitted_logs_string, hub_response_dict).
    """
    # ── build context from history ────────────────────────────────────────────
    hub_feedback = ""
    previous_answer = ""
    if history:
        last = history[-1]
        hub_feedback = json.dumps(last["hub_response"], ensure_ascii=False)
        previous_answer = last["submitted_logs"]
        if last["human_notes"]:
            hub_feedback += f"\n\nHuman notes: {last['human_notes']}"

    # ── step 1: filter with MCP tool ─────────────────────────────────────────
    console.rule(f"[bold]Iteration {iteration} – Filtering[/bold]")
    filter_result = mcp.call("filter_power_plant", {
        "lines": all_lines,
        "include_warn": True,
        "include_info": False,
    })
    filtered: list[str] = filter_result["filtered"]
    console.print(f"[cyan]Filtered to {filter_result['count']} lines "
                  f"({filter_result['tokens']} tokens)[/cyan]")

    # ── step 2: if already over budget, compress with MCP tool ───────────────
    if filter_result["tokens"] > TOKEN_BUDGET:
        console.print("[yellow]Over budget – running deduplication compression…[/yellow]")
        comp = mcp.call("compress_logs", {
            "lines": filtered,
            "token_budget": TOKEN_BUDGET,
            "strategy": "deduplicate",
        })
        filtered = comp["compressed"]
        console.print(f"[cyan]After compression: {comp['tokens']} tokens "
                      f"(dropped {comp['dropped']})[/cyan]")

    # ── step 3: DSPy agent decides final selection ────────────────────────────
    console.rule(f"[bold]Iteration {iteration} – LLM Analysis[/bold]")
    analyse = dspy.Predict(AnalyzeLogs)

    with console.status("[bold green]Agent thinking…"):
        pred = analyse(
            raw_lines=filtered,
            hub_feedback=hub_feedback,
            previous_answer=previous_answer,
            token_budget=TOKEN_BUDGET,
        )

    selected_logs: str = pred.selected_logs.strip()

    # ── step 4: verify token count ────────────────────────────────────────────
    token_check = mcp.call("count_tokens", {"text": selected_logs})
    tokens_used = token_check["tokens"]

    # ── step 5: if LLM returned too many tokens, trim via MCP ────────────────
    if tokens_used > TOKEN_BUDGET:
        console.print(f"[yellow]LLM output {tokens_used} tokens > budget "
                      f"– trimming with top_severity strategy…[/yellow]")
        lines_to_trim = selected_logs.splitlines()
        comp2 = mcp.call("compress_logs", {
            "lines": lines_to_trim,
            "token_budget": TOKEN_BUDGET,
            "strategy": "top_severity",
        })
        selected_logs = "\n".join(comp2["compressed"])
        tokens_used = comp2["tokens"]

    # ── display results ───────────────────────────────────────────────────────
    console.print(Panel(
        pred.reasoning,
        title="[bold green]Agent Reasoning[/bold green]",
        border_style="green",
    ))

    _display_log_table(selected_logs)

    token_color = "green" if tokens_used <= TOKEN_BUDGET else "red"
    console.print(f"\n[{token_color}]Token count: {tokens_used} / {TOKEN_BUDGET}[/{token_color}]")

    # ── submit to hub ─────────────────────────────────────────────────────────
    hub_response = submit_to_hub(selected_logs)

    console.print(Panel(
        json.dumps(hub_response, indent=2, ensure_ascii=False),
        title="[bold magenta]Hub Response[/bold magenta]",
        border_style="magenta",
    ))

    # ── evaluate with DSPy ────────────────────────────────────────────────────
    evaluate = dspy.Predict(EvaluateHubResponse)
    with console.status("[bold green]Evaluating hub response…"):
        eval_pred = evaluate(
            hub_response=json.dumps(hub_response, ensure_ascii=False),
            current_logs=selected_logs,
        )

    if eval_pred.is_success:
        console.print("[bold green]✓ Hub accepted the answer![/bold green]")
    else:
        console.print("[bold yellow]✗ Hub not satisfied.[/bold yellow]")
        console.print(f"[yellow]Action plan: {eval_pred.action_plan}[/yellow]")
        if eval_pred.missing_topics:
            console.print(f"[yellow]Missing topics: {', '.join(eval_pred.missing_topics)}[/yellow]")

    return selected_logs, hub_response


# ── display helpers ───────────────────────────────────────────────────────────

def _display_log_table(logs_string: str) -> None:
    table = Table(title="Selected Log Lines", show_lines=True, highlight=True)
    table.add_column("Timestamp", style="dim", no_wrap=True)
    table.add_column("Level", justify="center")
    table.add_column("Message")

    for line in logs_string.splitlines():
        import re
        m = re.match(r"(\[.*?\])\s*(\[.*?\])\s*(.*)", line)
        if m:
            ts, lvl, msg = m.group(1), m.group(2), m.group(3)
            color = {"CRIT": "red", "EMRG": "bold red", "WARN": "yellow"}.get(
                lvl.strip("[]"), "white"
            )
            table.add_row(ts, f"[{color}]{lvl}[/{color}]", msg)
        else:
            table.add_row("", "", line)

    console.print(table)


# ── human gate ────────────────────────────────────────────────────────────────

def human_gate(iteration: int) -> tuple[bool, str]:
    """
    Pause and ask human whether to continue.
    Returns (should_continue, human_notes).
    """
    console.rule("[bold yellow]⏸  Human review required[/bold yellow]")
    console.print(f"[bold]Completed iteration {iteration}.[/bold]")
    console.print("Review the hub response above before the next run.\n")

    notes = Prompt.ask(
        "[cyan]Enter notes for next iteration (or press Enter to skip)[/cyan]",
        default="",
    )
    proceed = Confirm.ask(
        "[bold yellow]Continue to next iteration?[/bold yellow]",
        default=False,
    )
    return proceed, notes


# ── main loop ─────────────────────────────────────────────────────────────────

def run_agent_loop() -> None:
    configure_dspy()
    history = load_history()
    iteration = len(history) + 1

    console.print(Panel(
        f"[bold]Log Analyzer – Agentic Loop[/bold]\n"
        f"Model : {OPENROUTER_MODEL}\n"
        f"Log   : {LOG_FILE_PATH}\n"
        f"Budget: {TOKEN_BUDGET} tokens\n"
        f"Hub   : {HUB_URL}\n"
        f"Prev. iterations: {len(history)}",
        title="[bold blue]Config[/bold blue]",
        border_style="blue",
    ))

    mcp_client = MCPClient()
    mcp_client.start()

    try:
        # Read log file once – reuse across iterations
        all_lines = read_all_lines(mcp_client)

        if not all_lines:
            console.print("[red]No lines read – check LOG_FILE_PATH in .env[/red]")
            return

        while True:
            logs, hub_resp = run_iteration(mcp_client, iteration, history, all_lines)

            proceed, notes = human_gate(iteration)

            append_iteration(history, iteration, logs, hub_resp, notes)

            if not proceed:
                console.print("[bold]Stopping. Session saved to session_history.json[/bold]")
                break

            iteration += 1

    finally:
        mcp_client.stop()
