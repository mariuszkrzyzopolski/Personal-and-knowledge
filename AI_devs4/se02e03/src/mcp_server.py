"""
MCP Server – log analysis tools.

Tools exposed:
  - read_log_file        : read raw log file, optionally paginated
  - filter_power_plant   : filter lines relevant to power plant / malfunction
  - count_tokens         : count tokens using cl100k_base (OpenAI tokenizer)
  - compress_logs        : rewrite / deduplicate logs to fit a token budget
  - get_session_history  : return hub responses from previous iterations
"""

import json
import re
from pathlib import Path

import tiktoken
from mcp.server.fastmcp import FastMCP

# ── tokenizer (same model as https://platform.openai.com/tokenizer) ──
_enc = tiktoken.get_encoding("cl100k_base")

mcp = FastMCP("log-tools")


# ──────────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────────

def _token_count(text: str) -> int:
    return len(_enc.encode(text))


# Power-plant keyword patterns (case-insensitive)
_POWER_PLANT_PATTERNS = re.compile(
    r"""
    REACTOR | SCRAM   | ECCS   | TURBINE  | COOLANT  | COOLPUMP |
    WTANK   | CORE    | NEUTRON| FUEL     | CONTROL[ _]ROD |
    PRESSURE_VESSEL   | PVRV   | STEAM    | CONDENSER|
    GENERATOR| TRANSFORMER|BREAKER|
    PWR\d+  |                         # power supply units
    VALVE   | PUMP    | INTERLOCK|TRIP |
    FIRMWARE| CTRL-\d+|               # firmware / controllers tied to plant
    TEMP[-_]\d+|                      # temperature sensors
    SOL-\d+ |                         # solenoids
    MALF    | RUNAWAY | OVERSPEED|
    \[CRIT\]| \[EMRG\]               # always include CRIT/EMRG regardless
    """,
    re.VERBOSE | re.IGNORECASE,
)


# ──────────────────────────────────────────────────────────────────────────────
# tools
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def read_log_file(
    path: str,
    start_line: int = 0,
    max_lines: int = 500,
) -> dict:
    """
    Read raw lines from a log file.

    Args:
        path:       Absolute or relative path to the log file.
        start_line: 0-based line index to start reading from (for pagination).
        max_lines:  Maximum number of lines to return per call.

    Returns:
        {
          "lines":      list[str],
          "start_line": int,
          "end_line":   int,
          "total_lines":int,
          "has_more":   bool
        }
    """
    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}

    all_lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(all_lines)
    chunk = all_lines[start_line : start_line + max_lines]

    return {
        "lines": chunk,
        "start_line": start_line,
        "end_line": start_line + len(chunk) - 1,
        "total_lines": total,
        "has_more": (start_line + max_lines) < total,
    }


@mcp.tool()
def filter_power_plant(
    lines: list[str],
    include_warn: bool = True,
    include_info: bool = False,
) -> dict:
    """
    Filter log lines that relate to power-plant systems or malfunctions.

    Args:
        lines:        Raw log lines (strings).
        include_warn: Include [WARN] level lines that match (default True).
        include_info: Include [INFO] level lines that match (default False).

    Returns:
        {
          "filtered": list[str],
          "count":    int,
          "tokens":   int
        }
    """
    result = []
    for line in lines:
        level_match = re.search(r"\[(CRIT|EMRG|WARN|INFO|DEBUG)\]", line, re.IGNORECASE)
        level = level_match.group(1).upper() if level_match else "UNKNOWN"

        if not _POWER_PLANT_PATTERNS.search(line):
            continue

        if level in ("CRIT", "EMRG"):
            result.append(line)
        elif level == "WARN" and include_warn:
            result.append(line)
        elif level == "INFO" and include_info:
            result.append(line)

    joined = "\n".join(result)
    return {
        "filtered": result,
        "count": len(result),
        "tokens": _token_count(joined),
    }


@mcp.tool()
def count_tokens(text: str) -> dict:
    """
    Count tokens in a string using cl100k_base (same as
    https://platform.openai.com/tokenizer).

    Returns:
        {"tokens": int, "within_budget": bool, "budget": int}
    """
    # Import here to avoid circular; budget is just informational
    budget = 1500
    n = _token_count(text)
    return {"tokens": n, "within_budget": n <= budget, "budget": budget}


@mcp.tool()
def compress_logs(
    lines: list[str],
    token_budget: int = 1500,
    strategy: str = "deduplicate",
) -> dict:
    """
    Compress log lines to fit within a token budget.

    Strategies:
      "deduplicate" – remove lines whose message body is near-duplicate of a
                      previous one (keeps the most severe level per message
                      pattern).
      "top_severity" – keep only CRIT/EMRG, then fill remaining budget with WARN.
      "truncate"    – hard-truncate the joined string at the token limit
                      (last resort, may cut a line mid-way).

    Args:
        lines:        Log lines to compress.
        token_budget: Maximum token count for the output.
        strategy:     One of "deduplicate", "top_severity", "truncate".

    Returns:
        {
          "compressed": list[str],
          "tokens":     int,
          "dropped":    int,
          "strategy":   str
        }
    """
    if strategy == "deduplicate":
        seen: dict[str, str] = {}  # pattern -> best line
        severity_rank = {"CRIT": 3, "EMRG": 4, "WARN": 2, "INFO": 1, "DEBUG": 0}

        for line in lines:
            # normalise: strip timestamps + numeric suffixes to get a "message pattern"
            pattern = re.sub(r"\d+", "N", re.sub(r"^\[.*?\]\s*\[.*?\]\s*", "", line))
            pattern = pattern.strip().lower()

            level_m = re.search(r"\[(CRIT|EMRG|WARN|INFO|DEBUG)\]", line, re.IGNORECASE)
            rank = severity_rank.get((level_m.group(1).upper() if level_m else "INFO"), 1)

            if pattern not in seen:
                seen[pattern] = (rank, line)
            else:
                if rank > seen[pattern][0]:
                    seen[pattern] = (rank, line)

        candidates = [v[1] for v in seen.values()]

    elif strategy == "top_severity":
        crits = [l for l in lines if re.search(r"\[(CRIT|EMRG)\]", l, re.IGNORECASE)]
        warns = [l for l in lines if re.search(r"\[WARN\]", l, re.IGNORECASE)]
        candidates = crits + warns

    else:
        candidates = lines[:]

    # ── trim to token budget ──────────────────────────────────────────────────
    kept = []
    total_tokens = 0
    for line in candidates:
        line_tokens = _token_count(line + "\n")
        if total_tokens + line_tokens > token_budget:
            if strategy == "truncate":
                # try to fit a partial line
                remaining = token_budget - total_tokens
                if remaining > 5:
                    kept.append(line[:remaining * 4])  # ~4 chars/token heuristic
            break
        kept.append(line)
        total_tokens += line_tokens

    joined = "\n".join(kept)
    return {
        "compressed": kept,
        "tokens": _token_count(joined),
        "dropped": len(lines) - len(kept),
        "strategy": strategy,
    }


@mcp.tool()
def get_session_history(history_path: str = "session_history.json") -> dict:
    """
    Load the persisted session history (hub responses + iteration notes).

    Returns:
        {
          "iterations": list[{iteration, hub_response, notes, timestamp}],
          "count":      int
        }
    """
    p = Path(history_path)
    if not p.exists():
        return {"iterations": [], "count": 0}

    try:
        data = json.loads(p.read_text())
        return {"iterations": data, "count": len(data)}
    except Exception as e:
        return {"error": str(e), "iterations": [], "count": 0}


# ──────────────────────────────────────────────────────────────────────────────
# entry point (run as standalone MCP server via stdio)
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
