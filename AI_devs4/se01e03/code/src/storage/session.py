import json
import os
from typing import Dict, List, Any
from ..config import config

class SessionManager:
    """Manages session persistence using JSON file storage."""
    
    def __init__(self, session_file_path: str = None):
        self.session_file_path = session_file_path or config.SESSION_FILE_PATH
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._load_sessions()
    
    def _load_sessions(self) -> None:
        """Load sessions from JSON file."""
        try:
            if os.path.exists(self.session_file_path):
                with open(self.session_file_path, 'r', encoding='utf-8') as f:
                    self._sessions = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupted or unreadable, start with empty sessions
            print(f"Warning: Could not load sessions file: {e}")
            self._sessions = {}
    
    def _save_sessions(self) -> None:
        """Save sessions to JSON file."""
        try:
            with open(self.session_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._sessions, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save sessions file: {e}")
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get all messages for a session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {"messages": []}
        
        return self._sessions[session_id].get("messages", [])
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a session and persist."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {"messages": []}
        
        message = {"role": role, "content": content}
        self._sessions[session_id]["messages"].append(message)
        self._save_sessions()
    
    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        if session_id in self._sessions:
            self._sessions[session_id]["messages"] = []
            self._save_sessions()
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions (for debugging/admin purposes)."""
        return self._sessions.copy()

# Global session manager instance
session_manager = SessionManager()
