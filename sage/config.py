"""Configuration management for Project Sage."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, SecretStr


class SageConfig(BaseModel):
    """Configuration model for Sage project settings."""
    
    project_path: Path = Field(description="Root path of the project")
    
    # Primary configuration (used for indexing/embeddings)
    api_key: SecretStr = Field(description="Primary API key")
    llm_provider: str = Field(default="google", description="Primary LLM provider (google/anthropic/openai/ollama)")
    llm_model: str = Field(default="gemini-1.5-flash", description="Primary LLM model name")
    
    # Additional API keys for multi-provider support
    google_api_key: Optional[SecretStr] = Field(default=None, description="Google Gemini API key")
    anthropic_api_key: Optional[SecretStr] = Field(default=None, description="Anthropic Claude API key") 
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI GPT API key")
    
    # Document and embedding settings
    document_language: str = Field(default="en", description="Primary language of documents")
    embedding_model: str = Field(default="text-embedding-004", description="Embedding model name")
    embedding_provider: str = Field(default="auto", description="Embedding provider (auto/google/openai/ollama/huggingface)")
    
    # Processing settings
    chunk_size: int = Field(default=1000, description="Text chunk size for processing")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    
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
            data['api_key'] = SecretStr(data.get('api_key', ''))
            data['project_path'] = Path(data.get('project_path', self.project_path))
            return SageConfig(**data)
    
    def save(self, config: SageConfig) -> None:
        """Save configuration to file."""
        os.makedirs(self.config_path.parent, exist_ok=True)
        os.makedirs(self.db_path, exist_ok=True)
        
        data = config.dict()
        data['api_key'] = config.api_key.get_secret_value() if config.api_key else None
        data['project_path'] = str(config.project_path)
        
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