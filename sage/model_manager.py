"""Model management for dynamic LLM switching in Project Sage."""

from typing import Dict, List, Optional, Tuple
from pydantic import SecretStr
from sage.config import SageConfig
from sage.llm_client import LLMClient

try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


class ModelManager:
    """Manages multiple LLM models and dynamic switching."""
    
    # Available models by provider
    AVAILABLE_MODELS = {
        "google": [
            "gemini-1.5-flash", 
            "gemini-1.5-pro", 
            "gemini-2.0-flash-exp",
            "gemini-exp-1206"
        ],
        "anthropic": [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229", 
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-4-latest",
            "claude-4-preview"
        ],
        "openai": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview", 
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5-preview",
            "gpt-5-turbo",
            "o1-preview",
            "o1-mini"
        ],
        "ollama": [
            "llama3.1:8b", "llama3.1:70b", "llama3.1:405b",
            "llama3.2:1b", "llama3.2:3b",
            "mixtral:8x7b", "mixtral:8x22b", 
            "codellama:7b", "codellama:13b", "codellama:34b",
            "deepseek-coder:6.7b", "deepseek-coder:33b",
            "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b",
            "phi3:mini", "phi3:medium",
            "gemma2:2b", "gemma2:9b", "gemma2:27b",
            "mistral:7b", "neural-chat:7b", "orca-mini:3b", "vicuna:7b"
        ]
    }
    
    def __init__(self, config: SageConfig):
        self.config = config
        self.active_clients: Dict[str, LLMClient] = {}
        
        # Use chat provider/model as current, with fallback to legacy
        chat_provider, chat_model = config.get_chat_provider_model()
        self.current_provider = chat_provider
        self.current_model = chat_model
        
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models organized by provider."""
        return self.AVAILABLE_MODELS.copy()
        
    def get_configured_providers(self) -> List[str]:
        """Get list of providers that have API keys configured."""
        providers = []
        
        # Check if we have API keys for each provider
        if self._has_api_key("google"):
            providers.append("google")
        if self._has_api_key("anthropic"):
            providers.append("anthropic")
        if self._has_api_key("openai"):
            providers.append("openai")
        if HAS_OLLAMA:
            providers.append("ollama")  # Ollama doesn't need API keys
            
        return providers
        
    def _has_api_key(self, provider: str) -> bool:
        """Check if we have an API key for the given provider."""
        if provider == "google":
            return bool(self.config.google_api_key or 
                       (self.config.llm_provider == "google" and self.config.api_key))
        elif provider == "anthropic":
            return bool(self.config.anthropic_api_key or 
                       (self.config.llm_provider == "anthropic" and self.config.api_key))
        elif provider == "openai":
            return bool(self.config.openai_api_key or 
                       (self.config.llm_provider == "openai" and self.config.api_key))
        elif provider == "ollama":
            return HAS_OLLAMA
        return False
        
    def _get_api_key(self, provider: str) -> str:
        """Get API key for the given provider."""
        if provider == "google":
            if self.config.google_api_key:
                return self.config.google_api_key.get_secret_value()
            elif self.config.llm_provider == "google":
                return self.config.api_key.get_secret_value()
        elif provider == "anthropic":
            if self.config.anthropic_api_key:
                return self.config.anthropic_api_key.get_secret_value()
            elif self.config.llm_provider == "anthropic":
                return self.config.api_key.get_secret_value()
        elif provider == "openai":
            if self.config.openai_api_key:
                return self.config.openai_api_key.get_secret_value()
            elif self.config.llm_provider == "openai":
                return self.config.api_key.get_secret_value()
        elif provider == "ollama":
            return "not-required"
        return ""
        
    def switch_model(self, provider: str, model: str) -> bool:
        """Switch to a different model for chat interactions."""
        try:
            # Validate provider and model
            if provider not in self.AVAILABLE_MODELS:
                raise ValueError(f"Unsupported provider: {provider}")
                
            if model not in self.AVAILABLE_MODELS[provider]:
                # Allow custom models for Ollama
                if provider != "ollama":
                    raise ValueError(f"Model {model} not available for {provider}")
                    
            # Check if we have API key for this provider
            if not self._has_api_key(provider):
                raise ValueError(f"No API key configured for {provider}")
                
            # Update current settings
            self.current_provider = provider
            self.current_model = model
            
            # Update config runtime settings
            self.config.current_chat_provider = provider
            self.config.current_chat_model = model
            
            # Clear cached client to force recreation
            client_key = f"{provider}:{model}"
            if client_key in self.active_clients:
                del self.active_clients[client_key]
                
            return True
            
        except Exception as e:
            print(f"Failed to switch model: {e}")
            return False
            
    def get_current_model_info(self) -> Tuple[str, str]:
        """Get current provider and model."""
        return self.current_provider, self.current_model
        
    def get_llm_client(self) -> LLMClient:
        """Get LLM client for current model, creating if needed."""
        client_key = f"{self.current_provider}:{self.current_model}"
        
        if client_key not in self.active_clients:
            # Create a temporary config for this specific model
            temp_config = self.config.copy()
            temp_config.llm_provider = self.current_provider
            temp_config.llm_model = self.current_model
            
            # Set the appropriate API key
            api_key = self._get_api_key(self.current_provider)
            temp_config.api_key = SecretStr(api_key)
            
            # Create client with temporary config
            self.active_clients[client_key] = LLMClient(temp_config)
            
        return self.active_clients[client_key]
        
    def list_available_models(self) -> List[Tuple[str, str, bool]]:
        """List all available models with their availability status."""
        models = []
        configured_providers = self.get_configured_providers()
        
        for provider, model_list in self.AVAILABLE_MODELS.items():
            available = provider in configured_providers
            for model in model_list:
                models.append((provider, model, available))
                
        return models
        
    def get_model_description(self, provider: str, model: str) -> str:
        """Get a human-readable description of the model."""
        descriptions = {
            ("google", "gemini-1.5-flash"): "⚡ Fast, efficient model for most tasks",
            ("google", "gemini-1.5-pro"): "🧠 High-quality model for complex reasoning",
            ("google", "gemini-2.0-flash-exp"): "🚀 Latest experimental model with enhanced speed",
            
            ("anthropic", "claude-3-haiku-20240307"): "⚡ Fast, cost-effective model", 
            ("anthropic", "claude-3-sonnet-20240229"): "⚖️ Balanced performance and speed",
            ("anthropic", "claude-3-opus-20240229"): "🏆 Most capable Claude 3 model",
            ("anthropic", "claude-3-5-sonnet-20241022"): "🎯 Latest Claude 3.5 with improved capabilities",
            ("anthropic", "claude-4-latest"): "🔮 Future Claude 4 (when available)",
            
            ("openai", "gpt-4o"): "🖼️ Multimodal model with vision capabilities",
            ("openai", "gpt-4o-mini"): "💨 Faster, cheaper version of GPT-4o",
            ("openai", "o1-preview"): "🧮 Advanced reasoning model for complex problems",
            ("openai", "gpt-5-preview"): "🔮 Future GPT-5 (when available)",
            
            ("ollama", "llama3.1:8b"): "🦙 Fast local model, good for most tasks (4GB)",
            ("ollama", "llama3.1:70b"): "🦙 High-quality local model (40GB)",
            ("ollama", "mixtral:8x7b"): "🔀 Expert model, great for coding (26GB)",
            ("ollama", "codellama:7b"): "💻 Specialized coding model (3.8GB)",
        }
        
        return descriptions.get((provider, model), f"📋 {provider.title()} model")
        
    def get_recommended_models(self) -> Dict[str, Tuple[str, str]]:
        """Get recommended models for different use cases."""
        configured = self.get_configured_providers()
        
        recommendations = {}
        
        # Speed (fastest available)
        if "google" in configured:
            recommendations["speed"] = ("google", "gemini-2.0-flash-exp")
        elif "anthropic" in configured:
            recommendations["speed"] = ("anthropic", "claude-3-5-sonnet-20241022")
        elif "ollama" in configured:
            recommendations["speed"] = ("ollama", "llama3.2:3b")
            
        # Quality (best available)
        if "anthropic" in configured:
            recommendations["quality"] = ("anthropic", "claude-4-latest")
        elif "openai" in configured:
            recommendations["quality"] = ("openai", "gpt-5-preview")
        elif "ollama" in configured:
            recommendations["quality"] = ("ollama", "llama3.1:70b")
            
        # Reasoning (best for complex tasks)
        if "openai" in configured:
            recommendations["reasoning"] = ("openai", "o1-preview")
        elif "anthropic" in configured:
            recommendations["reasoning"] = ("anthropic", "claude-3-opus-20240229")
        elif "ollama" in configured:
            recommendations["reasoning"] = ("ollama", "qwen2.5:14b")
            
        # Coding (best for programming)
        if "openai" in configured:
            recommendations["coding"] = ("openai", "o1-preview") 
        elif "ollama" in configured:
            recommendations["coding"] = ("ollama", "codellama:13b")
        elif "anthropic" in configured:
            recommendations["coding"] = ("anthropic", "claude-3-5-sonnet-20241022")
            
        # Privacy (local only)
        if "ollama" in configured:
            recommendations["privacy"] = ("ollama", "llama3.1:8b")
            
        # Multilingual (best for international content)
        if "google" in configured:
            recommendations["multilingual"] = ("google", "gemini-1.5-pro")
        elif "anthropic" in configured:
            recommendations["multilingual"] = ("anthropic", "claude-3-5-sonnet-20241022")
        elif "openai" in configured:
            recommendations["multilingual"] = ("openai", "gpt-4o")
        elif "ollama" in configured:
            recommendations["multilingual"] = ("ollama", "qwen2.5:14b")
            
        # Budget (most cost-effective)
        if "google" in configured:
            recommendations["budget"] = ("google", "gemini-1.5-flash")
        elif "openai" in configured:
            recommendations["budget"] = ("openai", "gpt-4o-mini")
        elif "anthropic" in configured:
            recommendations["budget"] = ("anthropic", "claude-3-haiku-20240307")
        elif "ollama" in configured:
            recommendations["budget"] = ("ollama", "llama3.2:3b")
            
        return recommendations
    
    def get_embedding_info(self, provider: str) -> str:
        """Get information about embedding model used by provider."""
        embedding_info = {
            "google": "🎯 Uses text-embedding-004 - Best for multilingual content (Vietnamese, Chinese, etc.)",
            "anthropic": "⚠️ Uses OpenAI embeddings - Claude has no native embeddings", 
            "openai": "📊 Uses text-embedding-3-small - Good multilingual support",
            "ollama": "🔒 Uses local embeddings (nomic-embed-text) - Complete privacy"
        }
        return embedding_info.get(provider, "Unknown embedding model")
    
    def get_switching_tips(self) -> List[str]:
        """Get tips for effective model switching."""
        return [
            "💡 Index with Google (best embeddings), chat with any model",
            "⚡ Use fast models (Gemini Flash, Claude Haiku) for quick questions",
            "🧠 Switch to quality models (Claude 4, GPT-5) for complex analysis",
            "🔒 Use Ollama models for complete privacy (no cloud API calls)",
            "💻 Use coding models (o1-preview, CodeLlama) for programming tasks",
            "🌍 Google models have best multilingual embeddings for Vietnamese/Chinese",
            "💰 Local Ollama models have no ongoing costs after setup"
        ]
    
    def get_detailed_recommendations(self) -> Dict[str, Dict[str, str]]:
        """Get detailed recommendations with explanations."""
        configured = self.get_configured_providers()
        recommendations = self.get_recommended_models()
        
        detailed = {}
        
        for use_case, (provider, model) in recommendations.items():
            description = self.get_model_description(provider, model)
            embedding_info = self.get_embedding_info(provider)
            
            detailed[use_case] = {
                "provider": provider,
                "model": model, 
                "description": description,
                "embedding_info": embedding_info,
                "available": provider in configured
            }
            
        return detailed

    def get_provider_comparison(self) -> Dict[str, Dict[str, str]]:
        """Get comparison of all providers."""
        return {
            "google": {
                "name": "Google Gemini",
                "embeddings": "text-embedding-004 (Best multilingual)",
                "strengths": "Fast, multilingual, great embeddings",
                "best_for": "Vietnamese/Chinese content, speed + quality",
                "privacy": "Cloud (Google servers)"
            },
            "anthropic": {
                "name": "Anthropic Claude", 
                "embeddings": "OpenAI embeddings (no native embeddings)",
                "strengths": "Best reasoning, analysis, writing",
                "best_for": "Complex analysis, content creation",
                "privacy": "Cloud (Anthropic servers)"
            },
            "openai": {
                "name": "OpenAI GPT",
                "embeddings": "text-embedding-3-small (Good multilingual)", 
                "strengths": "Latest reasoning (o1), multimodal (GPT-4o)",
                "best_for": "Reasoning, coding, vision tasks",
                "privacy": "Cloud (OpenAI servers)"
            },
            "ollama": {
                "name": "Ollama (Local)",
                "embeddings": "Local nomic-embed-text (Complete privacy)",
                "strengths": "Complete privacy, no API costs",
                "best_for": "Privacy, offline use, no ongoing costs", 
                "privacy": "100% Local (your computer only)"
            }
        }