"""
Configuration for Malmo MCP Server.

Centralized configuration using environment variables.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
MALMO_DIR = os.getenv('MALMO_DIR', str(BASE_DIR.parent / 'malmo'))
MALMOENV_DIR = os.getenv('MALMOENV_DIR', str(Path(MALMO_DIR) / 'MalmoEnv'))
MISSIONS_DIR = os.getenv('MISSIONS_DIR', str(Path(MALMOENV_DIR) / 'missions'))

# API Keys - LLM Providers
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')

# Supported LLM providers
SUPPORTED_LLM_TYPES = ['gemini', 'claude', 'openrouter', 'cerebras', 'cloudflare']

# LLM Configuration
DEFAULT_LLM_MODEL = os.getenv('DEFAULT_LLM_MODEL', 'gemini-2.5-flash-lite')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1024'))

# Server Configuration
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', '8000'))

# Malmo Configuration
MALMO_PORT = int(os.getenv('MALMO_PORT', '9000'))
DEFAULT_MISSION = os.getenv('DEFAULT_MISSION', 'mobchase_single_agent.xml')

# Agent Configuration
DECISION_INTERVAL = float(os.getenv('DECISION_INTERVAL', '5.0'))
MAX_STEPS = int(os.getenv('MAX_STEPS', '1000'))

# Deployment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development, production
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'


def get_mission_path(mission_name: str = None) -> str:
    """Get full path to mission file."""
    if mission_name is None:
        mission_name = DEFAULT_MISSION
    return str(Path(MISSIONS_DIR) / mission_name)


def validate_config():
    """Validate that required configuration is present."""
    errors = []

    if not GOOGLE_API_KEY and not ANTHROPIC_API_KEY:
        errors.append("At least one API key (GOOGLE_API_KEY or ANTHROPIC_API_KEY) must be set")

    if not Path(MALMOENV_DIR).exists():
        errors.append(f"MalmoEnv directory not found: {MALMOENV_DIR}")

    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True


if __name__ == "__main__":
    # Test configuration
    print("Configuration:")
    print(f"  BASE_DIR: {BASE_DIR}")
    print(f"  MALMO_DIR: {MALMO_DIR}")
    print(f"  MALMOENV_DIR: {MALMOENV_DIR}")
    print(f"  MISSIONS_DIR: {MISSIONS_DIR}")
    print(f"  GOOGLE_API_KEY: {'set' if GOOGLE_API_KEY else 'not set'}")
    print(f"  DEFAULT_MISSION: {DEFAULT_MISSION}")
    print(f"  Mission path: {get_mission_path()}")

    try:
        validate_config()
        print("\n✅ Configuration valid!")
    except ValueError as e:
        print(f"\n❌ Configuration errors:\n{e}")
