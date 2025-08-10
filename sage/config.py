"""Configuration management for Project Sage."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, SecretStr


class SageConfig(BaseModel):
    """Configuration model for Sage project settings."""
    
    project_path: Path = Field(description="Root path of the project")
    
    # Primary configuration (used for indexing/embeddings) - DEPRECATED, kept for backwards compatibility
    api_key: SecretStr = Field(description="Primary API key (for backwards compatibility)")
    llm_provider: str = Field(default="google", description="Primary LLM provider (for backwards compatibility)")
    llm_model: str = Field(default="gemini-1.5-flash", description="Primary LLM model name (for backwards compatibility)")
    
    # Separate configuration for indexing vs chat
    index_provider: Optional[str] = Field(default=None, description="Provider for indexing/embeddings (google/anthropic/openai/ollama)")
    index_model: Optional[str] = Field(default=None, description="Model for indexing/embeddings")
    chat_provider: Optional[str] = Field(default=None, description="Default provider for chat (google/anthropic/openai/ollama)")  
    chat_model: Optional[str] = Field(default=None, description="Default model for chat")
    
    # Additional API keys for multi-provider support
    google_api_key: Optional[SecretStr] = Field(default=None, description="Google Gemini API key")
    anthropic_api_key: Optional[SecretStr] = Field(default=None, description="Anthropic Claude API key") 
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI GPT API key")
    
    # Document and embedding settings
    document_language: str = Field(default="en", description="Primary language of documents")
    embedding_model: str = Field(default="text-embedding-004", description="Embedding model name")
    embedding_provider: str = Field(default="auto", description="Embedding provider (auto/google/openai/ollama/huggingface)")
    
    # Processing settings - Enhanced for Vietnamese and complex documentation
    chunk_size: int = Field(default=1500, description="Text chunk size for processing")
    chunk_overlap: int = Field(default=300, description="Overlap between chunks")
    
    # Ollama settings
    ollama_url: Optional[str] = Field(default=None, description="Ollama base URL for local models")
    
    # Runtime settings (not saved to config)
    current_chat_provider: Optional[str] = Field(default=None, exclude=True, description="Current chat provider override")
    current_chat_model: Optional[str] = Field(default=None, exclude=True, description="Current chat model override")
    
    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
            Path: str
        }
    
    def get_index_provider_model(self) -> tuple[str, str]:
        """Get the provider and model to use for indexing/embeddings."""
        if self.index_provider and self.index_model:
            return self.index_provider, self.index_model
        # Backwards compatibility - use primary/llm settings
        return self.llm_provider, self.llm_model
    
    def get_chat_provider_model(self) -> tuple[str, str]:
        """Get the provider and model to use for chat."""
        # Check runtime override first
        if self.current_chat_provider and self.current_chat_model:
            return self.current_chat_provider, self.current_chat_model
        # Use dedicated chat settings if available
        if self.chat_provider and self.chat_model:
            return self.chat_provider, self.chat_model
        # Backwards compatibility - use primary/llm settings
        return self.llm_provider, self.llm_model
    
    def get_index_api_key(self) -> str:
        """Get the API key for the indexing provider."""
        provider, _ = self.get_index_provider_model()
        return self._get_provider_api_key(provider)
    
    def get_chat_api_key(self) -> str:
        """Get the API key for the chat provider."""
        provider, _ = self.get_chat_provider_model()
        return self._get_provider_api_key(provider)
    
    def _get_provider_api_key(self, provider: str) -> str:
        """Get API key for a specific provider."""
        if provider == "google":
            if self.google_api_key:
                return self.google_api_key.get_secret_value()
            elif self.llm_provider == "google":
                return self.api_key.get_secret_value()
        elif provider == "anthropic":
            if self.anthropic_api_key:
                return self.anthropic_api_key.get_secret_value()
            elif self.llm_provider == "anthropic":
                return self.api_key.get_secret_value()
        elif provider == "openai":
            if self.openai_api_key:
                return self.openai_api_key.get_secret_value()
            elif self.llm_provider == "openai":
                return self.api_key.get_secret_value()
        elif provider == "ollama":
            return "not-required"
        return ""


class ConfigManager:
    """Manages Sage configuration for a project."""
    
    CONFIG_FILE = ".sage/config.json"
    DB_DIR = ".sage/db"
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.config_path = self.project_path / self.CONFIG_FILE
        self.db_path = self.project_path / self.DB_DIR
        
    def exists(self) -> bool:
        """Check if configuration exists for this project."""
        return self.config_path.exists()
    
    def load(self) -> Optional[SageConfig]:
        """Load configuration from file."""
        if not self.exists():
            return None
            
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            
            # Handle SecretStr fields properly
            data['api_key'] = SecretStr(data.get('api_key', ''))
            if data.get('google_api_key'):
                data['google_api_key'] = SecretStr(data['google_api_key'])
            if data.get('anthropic_api_key'):
                data['anthropic_api_key'] = SecretStr(data['anthropic_api_key'])
            if data.get('openai_api_key'):
                data['openai_api_key'] = SecretStr(data['openai_api_key'])
                
            data['project_path'] = Path(data.get('project_path', self.project_path))
            
            # Handle new separate configuration fields  
            data['index_provider'] = data.get('index_provider')
            data['index_model'] = data.get('index_model')
            data['chat_provider'] = data.get('chat_provider')
            data['chat_model'] = data.get('chat_model')
            return SageConfig(**data)
    
    def save(self, config: SageConfig) -> None:
        """Save configuration to file."""
        os.makedirs(self.config_path.parent, exist_ok=True)
        os.makedirs(self.db_path, exist_ok=True)
        
        data = config.dict()
        
        # Handle SecretStr fields properly
        data['api_key'] = config.api_key.get_secret_value() if config.api_key else None
        data['google_api_key'] = config.google_api_key.get_secret_value() if config.google_api_key else None
        data['anthropic_api_key'] = config.anthropic_api_key.get_secret_value() if config.anthropic_api_key else None
        data['openai_api_key'] = config.openai_api_key.get_secret_value() if config.openai_api_key else None
        data['project_path'] = str(config.project_path)
        
        # Handle new separate configuration fields
        data['index_provider'] = config.index_provider
        data['index_model'] = config.index_model
        data['chat_provider'] = config.chat_provider
        data['chat_model'] = config.chat_model
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        # Add to .gitignore if it exists
        gitignore_path = self.project_path / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                content = f.read()
            if ".sage/" not in content:
                with open(gitignore_path, 'a') as f:
                    f.write("\n# Sage configuration\n.sage/\n")
    
    def get_db_path(self) -> Path:
        """Get the path to the vector database."""
        return self.db_path