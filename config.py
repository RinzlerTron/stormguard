"""Configuration module for StormGuard.

Loads settings from environment variables and provides
centralized configuration management.
"""

import os
from pathlib import Path


class Config(object):
    """Application configuration."""
    
    # AWS Settings
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID', '')
    S3_BUCKET = os.getenv('S3_BUCKET', 'stormguard-data')
    
    # Bedrock Settings
    BEDROCK_MODEL_ID = os.getenv(
        'BEDROCK_MODEL_ID',
        'anthropic.claude-sonnet-4-20250514'
    )
    BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID', '')
    BEDROCK_AGENT_ALIAS_ID = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
    
    # External API Keys
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    
    # Application Settings
    ENV = os.getenv('ENV', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Demo Settings
    DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / 'data'
    OUTPUT_DIR = DATA_DIR / 'output'
    
    # Agent Settings
    MAX_TOOL_CALLS = 20
    AGENT_TEMPERATURE = 0.7
    AGENT_MAX_TOKENS = 4096
    
    # Policy Thresholds
    AUTO_APPROVAL_THRESHOLD_USD = 50000
    PRICE_CHANGE_MAX_PCT = 10.0
    MIN_SERVICE_LEVEL_PCT = 95.0
    
    @classmethod
    def validate(cls):
        """Validate required configuration is present.
        
        Returns:
            tuple: (is_valid, missing_keys)
        """
        required_for_prod = [
            'AWS_ACCOUNT_ID',
            'S3_BUCKET',
        ]
        
        missing = []
        if cls.ENV == 'production':
            for key in required_for_prod:
                if not getattr(cls, key, None):
                    missing.append(key)
        
        return len(missing) == 0, missing
    
    @classmethod
    def to_dict(cls):
        """Convert config to dictionary (for logging).
        
        Returns:
            dict: Configuration values (with secrets masked)
        """
        config_dict = {}
        for key in dir(cls):
            if key.isupper():
                value = getattr(cls, key)
                # Mask sensitive values
                if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
                    value = '***' if value else ''
                config_dict[key] = value
        return config_dict


# Create singleton instance
config = Config()


def load_env_file(env_file='.env'):
    """Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file
    """
    env_path = Path(env_file)
    if not env_path.exists():
        return
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value


# Auto-load .env if it exists
load_env_file()
