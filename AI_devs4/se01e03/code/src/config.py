import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""
    
    # External API Configuration
    PACKAGE_API_URL: str = os.getenv("PACKAGE_API_URL", "https://hub.ag3nts.org/api/packages")
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "3000"))
    
    # Session Storage
    SESSION_FILE_PATH: str = os.getenv("SESSION_FILE_PATH", "sessions.json")
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        required_vars = [
            "INTERNAL_API_KEY",
            "OPENROUTER_API_KEY"
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Create a global config instance
config = Config()
