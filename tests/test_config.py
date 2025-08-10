"""Test configuration management."""

import pytest
import tempfile
import shutil
from pathlib import Path
from pydantic import SecretStr

from sage.config import SageConfig, ConfigManager


def test_sage_config_creation():
    """Test SageConfig model creation."""
    config = SageConfig(
        project_path=Path("/test/path"),
        api_key=SecretStr("test-key"),
        llm_provider="google",
        llm_model="gemini-1.5-flash"
    )
    
    assert config.project_path == Path("/test/path")
    assert config.api_key.get_secret_value() == "test-key"
    assert config.llm_provider == "google"
    assert config.llm_model == "gemini-1.5-flash"


def test_config_manager():
    """Test ConfigManager functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        config_manager = ConfigManager(project_path)
        
        # Test that config doesn't exist initially
        assert not config_manager.exists()
        assert config_manager.load() is None
        
        # Create and save config
        config = SageConfig(
            project_path=project_path,
            api_key=SecretStr("test-key"),
            llm_provider="google"
        )
        
        config_manager.save(config)
        
        # Test that config now exists and can be loaded
        assert config_manager.exists()
        loaded_config = config_manager.load()
        
        assert loaded_config is not None
        assert loaded_config.project_path == project_path
        assert loaded_config.api_key.get_secret_value() == "test-key"
        assert loaded_config.llm_provider == "google"