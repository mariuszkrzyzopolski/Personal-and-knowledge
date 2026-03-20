"""
DSPy signatures used by the log-analysis agent.
"""

import dspy


class AnalyzeLogs(dspy.Signature):
    """
    You are a nuclear/industrial power-plant incident analyst.
    Given raw log lines and optional feedback from a previous hub response,
    decide which log entries are relevant to power-plant systems or malfunctions,
    then produce a compressed version that fits within 1500 tokens.

    Rules:
    - Include CRIT/EMRG entries that involve plant systems.
    - Include WARN entries if they describe a physical anomaly (not pure IT noise).
    - Exclude INFO / DEBUG / pure-IT entries unless they directly caused or
      describe a plant failure.
    - The output `selected_logs` must be the final newline-joined string of
      selected log lines, ordered chronologically.
    - Do NOT invent or modify timestamps or content.
    - If hub_feedback is non-empty, address the feedback: add more context,
      include extra entries, or refocus as requested.
    """

    raw_lines: list[str] = dspy.InputField(desc="All log lines read from the file")
    hub_feedback: str = dspy.InputField(
        desc="Feedback text returned by hub from the previous iteration "
             "(empty string on first run)"
    )
    previous_answer: str = dspy.InputField(
        desc="The log string submitted in the previous iteration "
             "(empty string on first run)"
    )
    token_budget: int = dspy.InputField(desc="Maximum tokens allowed for selected_logs")

    selected_logs: str = dspy.OutputField(
        desc="Final newline-joined log lines, within token_budget tokens"
    )
    reasoning: str = dspy.OutputField(
        desc="Brief explanation of selection and compression decisions"
    )


class EvaluateHubResponse(dspy.Signature):
    """
    Parse a hub API response and decide what the next iteration should improve.
    Return a concise action plan for the next run.
    """

    hub_response: str = dspy.InputField(desc="Raw JSON or text response from the hub")
    current_logs: str = dspy.InputField(desc="The logs that were submitted")

    is_success: bool = dspy.OutputField(desc="True if hub accepted the answer as correct")
    action_plan: str = dspy.OutputField(
        desc="What to change / add / remove in the next iteration"
    )
    missing_topics: list[str] = dspy.OutputField(
        desc="Topics or systems the hub says are missing or unclear"
    )
