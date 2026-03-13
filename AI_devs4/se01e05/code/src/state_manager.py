import json
import os
from typing import Dict, Any, Set
from dataclasses import dataclass, asdict


@dataclass
class ExplorationState:
    auto_accepted_routes: Set[str]
    visited_routes: Set[str]
    found_flags: list
    discovered_actions: Dict[str, Any]
    rate_limit_info: Dict[str, Any]
    action_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'auto_accepted_routes': list(self.auto_accepted_routes),
            'visited_routes': list(self.visited_routes),
            'found_flags': self.found_flags,
            'discovered_actions': self.discovered_actions,
            'rate_limit_info': self.rate_limit_info,
            'action_count': self.action_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExplorationState':
        return cls(
            auto_accepted_routes=set(data.get('auto_accepted_routes', [])),
            visited_routes=set(data.get('visited_routes', [])),
            found_flags=data.get('found_flags', []),
            discovered_actions=data.get('discovered_actions', {}),
            rate_limit_info=data.get('rate_limit_info', {}),
            action_count=data.get('action_count', 0)
        )


class StateManager:
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = ExplorationState(
            auto_accepted_routes=set(),
            visited_routes=set(),
            found_flags=[],
            discovered_actions={},
            rate_limit_info={},
            action_count=0
        )
        self._load_state()
    
    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.state = ExplorationState.from_dict(data)
    
    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
    
    def update_actions(self, actions: Dict[str, Any]):
        self.state.discovered_actions = actions
        self.save_state()
    
    def mark_route_visited(self, route: str):
        self.state.visited_routes.add(route)
        self.save_state()
    
    def add_auto_accepted_route(self, route: str):
        self.state.auto_accepted_routes.add(route)
        self.save_state()
    
    def add_found_flag(self, flag: str):
        self.state.found_flags.append(flag)
        self.save_state()
    
    def increment_action_count(self):
        self.state.action_count += 1
        self.save_state()
    
    def is_route_auto_accepted(self, route: str) -> bool:
        return route in self.state.auto_accepted_routes
    
    def is_route_visited(self, route: str) -> bool:
        return route in self.state.visited_routes
