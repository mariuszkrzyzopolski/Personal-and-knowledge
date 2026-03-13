import requests
import time
from typing import Dict, Any, Optional
import os


class APIClient:
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config['api']['base_url']
        self.task = config['api']['task']
        self.api_key = os.getenv('API_KEY', config['api']['api_key'].replace('${API_KEY}', ''))
        self.max_retries = config['agent']['max_retries']
        self.retry_delay_base = config['agent']['retry_delay_base']
        self.default_wait = config['rate_limit']['default_wait']
        self.max_wait = config['rate_limit']['max_wait']
        
    def _build_payload(self, answer: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "apikey": self.api_key,
            "task": self.task,
            "answer": answer
        }
    
    def _parse_rate_limit(self, headers: Dict[str, str]) -> Optional[float]:
        if 'Retry-After' in headers:
            return float(headers['Retry-After'])
        if 'X-RateLimit-Reset' in headers:
            reset_time = float(headers['X-RateLimit-Reset'])
            current_time = time.time()
            return max(0, reset_time - current_time)
        return None
    
    def call(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"action": action}
        if params:
            payload.update(params)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    json=self._build_payload(payload),
                    headers={'Content-Type': 'application/json'}
                )
                
                # Handle rate limiting
                wait_time = self._parse_rate_limit(response.headers)
                if wait_time:
                    wait_time = min(wait_time, self.max_wait)
                    print(f"[RATE LIMIT] Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # Handle 503 errors with exponential backoff
                if response.status_code == 503:
                    wait = min(self.retry_delay_base ** attempt, self.max_wait)
                    print(f"[503] Retry {attempt + 1}/{self.max_retries}, waiting {wait:.1f}s...")
                    time.sleep(wait)
                    continue
                
                # Check for other errors
                response.raise_for_status()
                
                # Default wait between successful calls to avoid rate limiting
                time.sleep(self.default_wait)
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = min(self.retry_delay_base ** attempt, self.max_wait)
                print(f"[ERROR] {e}. Retry {attempt + 1}/{self.max_retries}, waiting {wait:.1f}s...")
                time.sleep(wait)
        
        raise Exception(f"Failed after {self.max_retries} attempts")
