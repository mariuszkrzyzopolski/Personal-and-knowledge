import os
import yaml
from dotenv import load_dotenv
from hitl_agent import HITLAgent


def load_config(config_path: str = "src/config.yaml") -> dict:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    load_dotenv()
    
    config = load_config()
    
    # Validate API keys
    api_key = os.getenv('API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("[ERROR] API_KEY not set. Please set it in .env file or config.yaml")
        return
    
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key or openrouter_key == 'your-openrouter-key-here':
        print("[ERROR] OPENROUTER_API_KEY not set. Please set it in .env file")
        return
    
    print("[INIT] Starting HITL Agent...")
    print(f"[INIT] API Endpoint: {config['api']['base_url']}")
    print(f"[INIT] Task: {config['api']['task']}")
    
    agent = HITLAgent(config)
    agent.explore()


if __name__ == "__main__":
    main()
