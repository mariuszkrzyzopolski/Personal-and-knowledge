import requests
from dotenv import load_dotenv
import os
from pathlib import Path
import json
import dspy

load_dotenv()

HUB_API_KEY = os.environ["HUB_API_KEY"]
HUB_URL = os.getenv("HUB_URL", "https://hub.ag3nts.org/verify")
HUB_INBOX_URL = os.getenv("HUB_INBOX_URL", "https://hub.ag3nts.org/api/zmail")
HUB_TASK = os.environ["HUB_TASK"]
HISTORY_PATH = Path("session_history.json")


def submit_findings_to_hub(password: str, date: str, confirmation_code: str) -> dict:
    """
    Submit all findings from mailbox (password, date, confirmation_code) to hub to get the {FLG:...} flag
    """
    payload = {
        "apikey": HUB_API_KEY,
        "task": HUB_TASK,
        "answer": {
            "password": password,
            "date": date,
            "confirmation_code": confirmation_code
        }
    }
    print("\n→ Submitting to hub...")
    try:
        r = requests.post(HUB_URL, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def getInbox(page: int = 1, perPage: int = 5) -> dict:
    """
    Return list of threads in your mailbox.
    
    Args:
        page: Optional. Integer >= 1. Default: 1.
        perPage: Optional. Integer between 5 and 20. Default: 5.
    """
    payload = {
        "apikey": HUB_API_KEY,
        "action": "getInbox",
        "page": page,
        "perPage": perPage
    }
    
    try:
        r = requests.post(HUB_INBOX_URL, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}
 
def getThread(threadID: int) -> dict:
    """
    Return rowID and messageID list for a selected thread. No message body.
    
    Args:
        threadID: Required. Numeric thread identifier.
    """
    payload = {
        "apikey": HUB_API_KEY,
        "action": "getThread",
        "threadID": threadID
    }
    
    try:
        r = requests.post(HUB_INBOX_URL, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}
 
def getMessages(ids) -> dict:
    """
    Return one or more messages by rowID/messageID (hash).
    
    Args:
        ids: Required. Numeric rowID, 32-char messageID, or an array of them.
    """
    payload = {
        "apikey": HUB_API_KEY,
        "action": "getMessages",
        "ids": ids
    }
    
    try:
        r = requests.post(HUB_INBOX_URL, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}
 
def search(query: str, page: int = 1, perPage: int = 5) -> dict:
    """
    Search messages with full-text style query and Gmail-like operators.
    
    Args:
        query: Required. Supports words, "phrase", -exclude, from:, to:, subject:, subject:"phrase", subject:(phrase), OR, AND. Missing operator means AND.
        page: Optional. Integer >= 1. Default: 1.
        perPage: Optional. Integer between 5 and 20. Default: 5.
    """
    payload = {
        "apikey": HUB_API_KEY,
        "action": "search",
        "query": query,
        "page": page,
        "perPage": perPage
    }
    
    try:
        r = requests.post(HUB_INBOX_URL, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def save_history(history: dspy.History) -> None:
    """
    Save conversation history to file
    """
    history_data = []
    for msg in history.messages:
        if isinstance(msg, dict):
            history_data.append(msg)
        else:
            history_data.append({"content": str(msg)})
    
    with open(HISTORY_PATH, "w") as f:
        json.dump(history_data, f, indent=2)

def load_history() -> dspy.History:
    """
    Load conversation history from file
    """
    if not HISTORY_PATH.exists():
        return dspy.History(messages=[])
    with open(HISTORY_PATH, "r") as f:
        history_data = json.load(f)    
    return dspy.History(messages=history_data)