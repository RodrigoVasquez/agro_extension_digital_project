"""Test configuration and fixtures."""
import pytest
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ.setdefault("APP_URL", "https://test-agent.example.com")
os.environ.setdefault("ESTANDAR_AA_APP_NAME", "test_aa")
os.environ.setdefault("ESTANDAR_PP_APP_NAME", "test_pp")
os.environ.setdefault("ESTANDAR_AA_FACEBOOK_APP", "123456789")
os.environ.setdefault("ESTANDAR_PP_FACEBOOK_APP", "987654321")
os.environ.setdefault("WSP_TOKEN", "test_token")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path/to/credentials.json")

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for tests."""
    test_vars = {
        "APP_URL": "https://test-agent.example.com",
        "ESTANDAR_AA_APP_NAME": "test_aa",
        "ESTANDAR_PP_APP_NAME": "test_pp", 
        "ESTANDAR_AA_FACEBOOK_APP": "123456789",
        "ESTANDAR_PP_FACEBOOK_APP": "987654321",
        "WSP_TOKEN": "test_token",
        "WHATSAPP_API_URL_AA": "https://graph.facebook.com/v17.0/123456789",
        "WHATSAPP_API_URL_PP": "https://graph.facebook.com/v17.0/987654321",
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    
    return test_vars
