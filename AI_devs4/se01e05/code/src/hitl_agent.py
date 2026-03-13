import re
import json
import os
from typing import Dict, Any, List, Optional
from openrouter import OpenRouter
from api_client import APIClient
from state_manager import StateManager, ExplorationState


class HITLAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_client = APIClient(config)
        self.state_manager = StateManager(config['agent']['state_file'])
        
        # Initialize OpenRouter client
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_key:
            config_key = config['openrouter']['api_key']
            if config_key.startswith('${') and config_key.endswith('}'):
                raise ValueError("OPENROUTER_API_KEY environment variable is required but not set")
            openrouter_key = config_key
        
        self.openrouter = OpenRouter(api_key=openrouter_key)
        self.model = config['openrouter']['model']
        self.hitl_default = config['agent']['hitl_default']
        self.help_refresh_interval = config['agent']['help_refresh_interval']
        
        # Get initial steering direction from user
        self.global_steering = input("Enter global steering direction (or press Enter for none): ").strip() or None
    
    def extract_flags(self, response: Dict[str, Any]) -> List[str]:
        text = json.dumps(response)
        flags = re.findall(r'\{FLG:[^}]+\}', text)
        return flags
    
    def call_help(self) -> Dict[str, Any]:
        response = self.api_client.call("help")
        if response.get('ok'):
            actions = response.get('help', {}).get('actions', [])
            self.state_manager.update_actions({a['action']: a for a in actions})
            return response
        return response
    
    def generate_plan(self, route: str, current_state: ExplorationState, steering: Optional[str] = None) -> Dict[str, Any]:
        # Combine global steering with local steering
        combined_steering = steering
        if self.global_steering:
            combined_steering = f"{self.global_steering}. {steering}" if steering else self.global_steering
        
        prompt = f"""You are an API exploration agent. Generate a sequence of actions to explore this route and find flags.

MAIN GOAL: Reconfigure route X-01 to be open to receive the flag "{{FLG:...}}"
Focus on actions that might help open routes or configure route settings.

Current State:
- Routes explored: {sorted(current_state.visited_routes)}
- Available actions: {list(current_state.discovered_actions.keys())}
- Target route: {route}
- Found flags: {current_state.found_flags}

Available Actions:
{json.dumps(current_state.discovered_actions, indent=2)}

{f"Steering instruction: {combined_steering}" if combined_steering else ""}

Return ONLY a JSON object with this exact format:
{{
  "actions": [
    {{"action": "action_name", "params": {{"param": "value"}}}}
  ],
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.openrouter.chat.send(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are an API exploration assistant. Generate valid JSON only."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"actions": [], "reasoning": "Could not parse response"}
        except Exception as e:
            print(f"[ERROR] OpenRouter generation failed: {e}")
            return {"actions": [], "reasoning": f"Error: {str(e)}"}
    
    def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.state_manager.increment_action_count()
        
        # Refresh help periodically to discover new actions
        if self.state_manager.state.action_count % self.help_refresh_interval == 0:
            print("[INFO] Refreshing help to discover new actions...")
            self.call_help()
        
        response = self.api_client.call(action, params)
        flags = self.extract_flags(response)
        
        if flags:
            for flag in flags:
                print(f"🎯 FLAG FOUND: {flag}")
                self.state_manager.add_found_flag(flag)
        
        return response
    
    def hitl_check_before_route(self, route: str, plan: Dict[str, Any]) -> bool:
        if not self.hitl_default or self.state_manager.is_route_auto_accepted(route):
            return True
        
        print(f"\n{'='*60}")
        print(f"[PLAN] Route: {route}")
        print(f"[PLAN] Reasoning: {plan.get('reasoning', 'N/A')}")
        print(f"[PLAN] Actions:")
        for i, action in enumerate(plan.get('actions', []), 1):
            print(f"  {i}. {action['action']}: {action.get('params', {})}")
        print(f"{'='*60}")
        
        choice = input("Execute? (y/n/auto/steer): ").strip().lower()
        
        if choice == 'n':
            return False
        elif choice == 'auto':
            self.state_manager.add_auto_accepted_route(route)
            print(f"[INFO] Route '{route}' added to auto-accept list")
        elif choice == 'steer':
            direction = input("Enter steering direction/instruction: ").strip()
            if direction:
                plan = self.generate_plan(route, self.state_manager.state, steering=direction)
                print(f"[STEER] Added instruction: {direction}")
                print(f"[PLAN] Updated Reasoning: {plan.get('reasoning', 'N/A')}")
                print(f"[PLAN] Updated Actions:")
                for i, action in enumerate(plan.get('actions', []), 1):
                    print(f"  {i}. {action['action']}: {action.get('params', {})}")
                print(f"{'='*60}")
                choice = input("Execute updated plan? (y/n): ").strip().lower()
                if choice == 'n':
                    return False
        
        return True
    
    def hitl_check_after_route(self, route: str) -> bool:
        print(f"\n{'='*60}")
        print(f"[COMPLETE] Route {route} finished")
        print(f"[COMPLETE] Flags found in this route: {self.extract_flags_from_route(route)}")
        print(f"[COMPLETE] Total flags found: {len(self.state_manager.state.found_flags)}")
        print(f"{'='*60}")
        
        choice = input("Continue to next route? (y/n/steer): ").strip().lower()
        if choice == 'n':
            return False
        elif choice == 'steer':
            new_steering = input("Enter new global steering direction: ").strip()
            if new_steering:
                self.global_steering = new_steering
                print(f"[INFO] Global steering updated: {self.global_steering}")
        
        return True
    
    def extract_flags_from_route(self, route: str) -> List[str]:
        return [f for f in self.state_manager.state.found_flags if route.lower() in f.lower() or route.lower() in str(f).lower()]
    
    def explore(self):
        print("[START] Beginning API exploration...")
        
        # Get initial help
        help_response = self.call_help()
        print(f"[INFO] Discovered {len(self.state_manager.state.discovered_actions)} actions")
        
        # Get route format from help
        route_format = help_response.get('help', {}).get('route_format', '')
        print(f"[INFO] Route format: {route_format}")
        
        # Generate initial routes to explore
        routes = self._generate_routes(route_format)
        print(f"[INFO] Will explore {len(routes)} routes")
        
        for route in routes:
            if self.state_manager.is_route_visited(route):
                print(f"[SKIP] Route {route} already visited")
                continue
            
            print(f"\n[EXPLORE] Starting route: {route}")
            
            # Generate plan
            plan = self.generate_plan(route, self.state_manager.state)
            
            # HITL before execution
            if not self.hitl_check_before_route(route, plan):
                print(f"[SKIP] Skipping route {route}")
                continue
            
            # Execute plan
            for action in plan.get('actions', []):
                action_name = action['action']
                params = action.get('params', {})
                print(f"[EXEC] {action_name}({params})")
                
                try:
                    response = self.execute_action(action_name, params)
                    print(f"[OK] Response: {json.dumps(response, indent=2)[:200]}...")
                except Exception as e:
                    print(f"[ERROR] Failed to execute {action_name}: {e}")
                    break
            
            # Mark as visited
            self.state_manager.mark_route_visited(route)
            
            # HITL after route completion
            if not self.hitl_check_after_route(route):
                print("[STOP] Exploration stopped by user")
                break
        
        print(f"\n[SUMMARY] Exploration complete")
        print(f"[SUMMARY] Routes visited: {len(self.state_manager.state.visited_routes)}")
        print(f"[SUMMARY] Flags found: {self.state_manager.state.found_flags}")
        print(f"[SUMMARY] Auto-accepted routes: {len(self.state_manager.state.auto_accepted_routes)}")
    
    def _generate_routes(self, route_format: str) -> List[str]:
        routes = []
        if 'a-z' in route_format and '0-9' in route_format:
            for letter in ['a', 'b', 'c', 'd', 'e']:
                for num in range(1, 13):
                    routes.append(f"{letter}-{num}")
        return routes
