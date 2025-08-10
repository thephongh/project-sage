"""GUI setup window for Project Sage initialization."""

import customtkinter as ctk
import tkinter as tk
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional, Callable
from sage.config import SageConfig, ConfigManager


class SetupWindow:
    """Simple GUI window for project setup."""
    
    LANGUAGES = {
        "English": "eng",
        "Vietnamese": "vie",
        "Chinese (Simplified)": "chi_sim",
        "Chinese (Traditional)": "chi_tra",
        "Japanese": "jpn",
        "Korean": "kor",
        "Spanish": "spa",
        "French": "fra",
        "German": "deu",
        "Russian": "rus",
        "Arabic": "ara",
        "Thai": "tha"
    }
    
    PROVIDERS = {
        "Google Gemini": "google",
        "Anthropic Claude": "anthropic", 
        "OpenAI GPT": "openai",
        "Ollama (Local)": "ollama"
    }
    
    MODEL_DESCRIPTIONS = {
        # Google Gemini Models
        "gemini-1.5-flash": "⚡ FAST & EFFICIENT - Best for general tasks, quick responses\nEmbeddings: Excellent multilingual support (Vietnamese, Chinese, etc.)\nSpeed: Very Fast | Cost: Low | Quality: Good",
        "gemini-1.5-pro": "🧠 HIGH QUALITY - Best for complex reasoning and analysis\nEmbeddings: Best-in-class semantic understanding\nSpeed: Medium | Cost: Medium | Quality: Excellent",
        "gemini-2.0-flash": "🚀 LATEST STABLE - Cutting-edge speed + quality\nEmbeddings: Latest Google embedding technology\nSpeed: Very Fast | Cost: Low | Quality: Very Good",
        "gemini-2.0-flash-exp": "🔬 EXPERIMENTAL - Latest experimental features\nEmbeddings: Advanced experimental Google tech\nSpeed: Very Fast | Cost: Low | Quality: Experimental",
        "gemini-2.5-flash": "✨ NEWEST RELEASE - Most efficient workhorse model\nEmbeddings: Latest Google embedding with thinking\nSpeed: Very Fast | Cost: Very Low | Quality: Excellent",
        "gemini-2.5-pro": "🧠 STATE-OF-THE-ART - Best thinking model for complex reasoning\nEmbeddings: Latest Google embedding with deep reasoning\nSpeed: Medium | Cost: Medium | Quality: Excellent (Thinking)",
        "gemini-2.0-pro": "🧠 PRO QUALITY - Enhanced reasoning with 2M context\nEmbeddings: Best-in-class semantic understanding\nSpeed: Medium | Cost: Medium | Quality: Excellent",
        "gemini-exp-1206": "🔬 RESEARCH - Google's experimental research model\nEmbeddings: Advanced experimental features\nSpeed: Medium | Cost: Medium | Quality: Experimental",
        
        # Anthropic Claude Models
        "claude-3-haiku-20240307": "💨 FASTEST CLAUDE - Quick responses, cost-effective\nEmbeddings: Uses OpenAI (Anthropic has no embeddings)\nSpeed: Very Fast | Cost: Low | Quality: Good",
        "claude-3-sonnet-20240229": "⚖️ BALANCED - Good balance of speed and capability\nEmbeddings: Uses OpenAI embeddings\nSpeed: Fast | Cost: Medium | Quality: Very Good",
        "claude-3-opus-20240229": "🏆 MOST CAPABLE - Best Claude 3, complex tasks\nEmbeddings: Uses OpenAI embeddings\nSpeed: Slow | Cost: High | Quality: Excellent",
        "claude-3-5-sonnet-20241022": "🎯 LATEST CLAUDE - Enhanced reasoning and coding\nEmbeddings: Uses OpenAI embeddings\nSpeed: Fast | Cost: Medium | Quality: Excellent",
        "claude-3-5-haiku-20241022": "⚡ FAST CLAUDE 3.5 - Quick and smart\nEmbeddings: Uses OpenAI embeddings\nSpeed: Very Fast | Cost: Low | Quality: Very Good",
        "claude-sonnet-4": "🚀 CLAUDE SONNET 4 - Latest production model (available now)\nEmbeddings: Uses OpenAI embeddings\nSpeed: Fast | Cost: Medium | Quality: Excellent",
        "claude-opus-4-1-20250805": "🏆 CLAUDE OPUS 4.1 - Most capable Claude model\nEmbeddings: Uses OpenAI embeddings\nSpeed: Medium | Cost: High | Quality: Excellent",
        "claude-4-latest": "🔮 FUTURE CLAUDE 4 - Next generation placeholder\nEmbeddings: Uses OpenAI embeddings\nSpeed: TBD | Cost: TBD | Quality: Expected Excellent",
        
        # OpenAI GPT Models
        "gpt-3.5-turbo": "💰 COST-EFFECTIVE - Good for basic tasks, very cheap\nEmbeddings: Good multilingual support\nSpeed: Fast | Cost: Very Low | Quality: Good",
        "gpt-4": "🧠 SMART GPT-4 - Reliable for complex reasoning\nEmbeddings: Excellent semantic understanding\nSpeed: Medium | Cost: Medium | Quality: Very Good",
        "gpt-4-turbo": "⚡ FASTER GPT-4 - Improved speed, same quality\nEmbeddings: Excellent with good speed\nSpeed: Fast | Cost: Medium | Quality: Very Good",
        "gpt-4-turbo-preview": "🔬 GPT-4 PREVIEW - Latest GPT-4 improvements\nEmbeddings: Latest OpenAI embedding tech\nSpeed: Fast | Cost: Medium | Quality: Very Good",
        "gpt-4o": "🖼️ MULTIMODAL - Vision + text, very capable\nEmbeddings: Advanced multimodal understanding\nSpeed: Fast | Cost: Medium | Quality: Excellent",
        "gpt-4o-mini": "💨 FAST GPT-4O - Cheaper, faster version of GPT-4o\nEmbeddings: Good speed and quality balance\nSpeed: Very Fast | Cost: Low | Quality: Very Good",
        "gpt-5": "🚀 GPT-5 - Latest generation model (available now)\nEmbeddings: Best-in-class OpenAI embeddings\nSpeed: Medium | Cost: High | Quality: Excellent",
        "gpt-5-mini": "⚡ GPT-5 MINI - Faster, cost-effective GPT-5\nEmbeddings: Excellent with speed optimization\nSpeed: Fast | Cost: Medium | Quality: Very Good",
        "gpt-5-nano": "💨 GPT-5 NANO - Ultra-fast GPT-5 variant\nEmbeddings: Good speed and efficiency\nSpeed: Very Fast | Cost: Low | Quality: Good",
        "o1-preview": "🧮 REASONING EXPERT - Best for math, logic, complex problems\nEmbeddings: Specialized for analytical tasks\nSpeed: Slow | Cost: High | Quality: Excellent (Reasoning)",
        "o1-mini": "🧮 MINI REASONING - Faster reasoning model\nEmbeddings: Good for logical tasks\nSpeed: Medium | Cost: Medium | Quality: Very Good (Reasoning)",
        
        # Ollama Local Models
        "llama3.1:8b": "🦙 FAST LOCAL - Best general local model\nEmbeddings: Local (nomic-embed-text) - Private\nSpeed: Fast | RAM: 8GB | Quality: Very Good | Privacy: 100%",
        "llama3.1:70b": "🦙 BEST LOCAL - Highest quality local model\nEmbeddings: Local (nomic-embed-text) - Private\nSpeed: Slow | RAM: 64GB | Quality: Excellent | Privacy: 100%",
        "llama3.1:405b": "🦙 MASSIVE LOCAL - Research-grade model (huge)\nEmbeddings: Local (nomic-embed-text) - Private\nSpeed: Very Slow | RAM: 200GB+ | Quality: Excellent | Privacy: 100%",
        "llama3.2:1b": "🦙 TINY LOCAL - Ultra-fast, minimal resources\nEmbeddings: Local - Private\nSpeed: Very Fast | RAM: 2GB | Quality: Good | Privacy: 100%",
        "llama3.2:3b": "🦙 SMALL LOCAL - Good balance of speed and size\nEmbeddings: Local - Private\nSpeed: Very Fast | RAM: 4GB | Quality: Very Good | Privacy: 100%",
        "mixtral:8x7b": "🔀 EXPERT LOCAL - Great for coding and technical\nEmbeddings: Local - Private\nSpeed: Medium | RAM: 32GB | Quality: Excellent | Privacy: 100%",
        "mixtral:8x22b": "🔀 LARGE EXPERT - Highest quality expert model\nEmbeddings: Local - Private\nSpeed: Slow | RAM: 80GB | Quality: Excellent | Privacy: 100%",
        "codellama:7b": "💻 CODE SPECIALIST - Best for programming tasks\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 8GB | Quality: Excellent (Code) | Privacy: 100%",
        "codellama:13b": "💻 BETTER CODE - More capable coding model\nEmbeddings: Local - Private\nSpeed: Medium | RAM: 16GB | Quality: Excellent (Code) | Privacy: 100%",
        "codellama:34b": "💻 EXPERT CODE - Best local coding model\nEmbeddings: Local - Private\nSpeed: Slow | RAM: 32GB | Quality: Excellent (Code) | Privacy: 100%",
        "deepseek-coder:6.7b": "👨‍💻 DEEPSEEK CODE - Alternative coding specialist\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 8GB | Quality: Very Good (Code) | Privacy: 100%",
        "deepseek-coder:33b": "👨‍💻 LARGE DEEPSEEK - More capable coding\nEmbeddings: Local - Private\nSpeed: Slow | RAM: 32GB | Quality: Excellent (Code) | Privacy: 100%",
        "qwen2.5:7b": "🧠 QWEN REASONING - Good for analysis and math\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 8GB | Quality: Very Good | Privacy: 100%",
        "qwen2.5:14b": "🧠 BETTER QWEN - Enhanced reasoning capabilities\nEmbeddings: Local - Private\nSpeed: Medium | RAM: 16GB | Quality: Excellent | Privacy: 100%",
        "qwen2.5:32b": "🧠 LARGE QWEN - Best reasoning local model\nEmbeddings: Local - Private\nSpeed: Slow | RAM: 32GB | Quality: Excellent | Privacy: 100%",
        "phi3:mini": "🔬 PHI3 MINI - Microsoft's efficient model\nEmbeddings: Local - Private\nSpeed: Very Fast | RAM: 4GB | Quality: Good | Privacy: 100%",
        "phi3:medium": "🔬 PHI3 MEDIUM - Balanced Microsoft model\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 8GB | Quality: Very Good | Privacy: 100%",
        "gemma2:2b": "💎 TINY GEMMA - Google's small efficient model\nEmbeddings: Local - Private\nSpeed: Very Fast | RAM: 4GB | Quality: Good | Privacy: 100%",
        "gemma2:9b": "💎 GEMMA BALANCED - Good Google local model\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 12GB | Quality: Very Good | Privacy: 100%",
        "gemma2:27b": "💎 LARGE GEMMA - Google's capable local model\nEmbeddings: Local - Private\nSpeed: Medium | RAM: 32GB | Quality: Excellent | Privacy: 100%",
        "mistral:7b": "🌪️ MISTRAL - Well-rounded European model\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 8GB | Quality: Very Good | Privacy: 100%",
        "neural-chat:7b": "💬 NEURAL CHAT - Optimized for conversations\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 8GB | Quality: Good (Chat) | Privacy: 100%",
        "orca-mini:3b": "🐋 ORCA MINI - Microsoft-inspired small model\nEmbeddings: Local - Private\nSpeed: Very Fast | RAM: 4GB | Quality: Good | Privacy: 100%",
        "vicuna:7b": "🦙 VICUNA - Fine-tuned conversation model\nEmbeddings: Local - Private\nSpeed: Fast | RAM: 8GB | Quality: Very Good (Chat) | Privacy: 100%",
        "custom-model": "🔧 CUSTOM MODEL - Enter your own Ollama model name\nEmbeddings: Local - Private\nUse any model you have installed in Ollama | Privacy: 100%"
    }
    
    MODELS = {
        "google": [
            "gemini-1.5-flash", 
            "gemini-1.5-pro", 
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-pro",
            "gemini-exp-1206"
        ],
        "anthropic": [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229", 
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-sonnet-4",
            "claude-opus-4-1-20250805",
            "claude-4-latest"  # Future placeholder
        ],
        "openai": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview", 
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5",          # Available now
            "gpt-5-mini",     # Available now
            "gpt-5-nano",     # Available now
            "o1-preview",
            "o1-mini"
        ],
        "ollama": [
            "llama3.1:8b",
            "llama3.1:70b", 
            "llama3.1:405b",
            "llama3.2:1b",
            "llama3.2:3b",
            "mixtral:8x7b",
            "mixtral:8x22b",
            "codellama:7b",
            "codellama:13b",
            "codellama:34b",
            "deepseek-coder:6.7b",
            "deepseek-coder:33b",
            "qwen2.5:7b",
            "qwen2.5:14b",
            "qwen2.5:32b",
            "phi3:mini",
            "phi3:medium",
            "gemma2:2b",
            "gemma2:9b",
            "gemma2:27b",
            "mistral:7b",
            "neural-chat:7b",
            "orca-mini:3b",
            "vicuna:7b",
            "custom-model"  # Allow custom model names
        ]
    }
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.config_manager = ConfigManager(project_path)
        self.result: Optional[SageConfig] = None
        
        # Set appearance mode
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Project Sage Setup - Separate Index & Chat Models")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # Tooltip for model descriptions
        self.tooltip_window = None
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Title
        title = ctk.CTkLabel(
            self.root, 
            text="Project Sage Setup",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # Project path frame
        path_frame = ctk.CTkFrame(self.root)
        path_frame.pack(pady=10, padx=20, fill="x")
        
        path_label = ctk.CTkLabel(path_frame, text="Project Directory:")
        path_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        path_value = ctk.CTkLabel(
            path_frame, 
            text=str(self.project_path),
            font=ctk.CTkFont(family="monospace")
        )
        path_value.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Create main notebook for separate model selection
        self.model_notebook = ctk.CTkTabview(self.root)
        self.model_notebook.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Indexing (Embedding) Configuration Tab
        self.index_tab = self.model_notebook.add("📚 Indexing & Embeddings")
        self._create_index_config_section()
        
        # Chat Configuration Tab  
        self.chat_tab = self.model_notebook.add("💬 Chat & Responses")
        self._create_chat_config_section()
        
        # API Keys Tab
        self.api_tab = self.model_notebook.add("🔑 API Keys")
        self._create_api_keys_section()
        
        # Language selection
        lang_label = ctk.CTkLabel(self.root, text="Document Language (for OCR):")
        lang_label.pack(anchor="w", padx=30, pady=(10, 0))
        
        self.lang_var = ctk.StringVar(value="English")
        lang_menu = ctk.CTkOptionMenu(
            self.root,
            values=list(self.LANGUAGES.keys()),
            variable=self.lang_var
        )
        lang_menu.pack(padx=30, pady=5, fill="x")
        
        # Buttons frame
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=30)
        
        # Initialize button
        init_button = ctk.CTkButton(
            button_frame,
            text="Initialize Project",
            command=self._on_initialize,
            width=150
        )
        init_button.pack(side="left", padx=10)
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=150,
            fg_color="gray"
        )
        cancel_button.pack(side="left", padx=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.root,
            text="",
            text_color="gray"
        )
        self.status_label.pack(pady=10)
        
    def _show_model_info(self):
        """Show detailed model information window."""
        info_window = ctk.CTkToplevel(self.root)
        info_window.title("Model Selection Guide")
        info_window.geometry("900x700")
        info_window.transient(self.root)
        info_window.grab_set()
        
        # Title
        title = ctk.CTkLabel(
            info_window,
            text="🤖 Model Selection Guide",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        
        # Scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(info_window)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Embedding impact notice
        embedding_notice = ctk.CTkLabel(
            scrollable_frame,
            text="⚠️ IMPORTANT: Embedding Model Impact\n\n" + 
            "The provider you choose determines the embedding model used for indexing:\n" +
            "• Google: text-embedding-004 (Best multilingual, Vietnamese support)\n" +
            "• Anthropic: Uses OpenAI embeddings (Claude has no embeddings)\n" +
            "• OpenAI: text-embedding-3-small (Good multilingual support)\n" +
            "• Ollama: Local embeddings (Complete privacy, no cloud)\n\n" +
            "You can switch chat models anytime, but changing embedding providers requires re-indexing!",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="orange",
            wraplength=850,
            justify="left"
        )
        embedding_notice.pack(pady=(0, 20), fill="x")
        
        # Provider sections
        providers = [
            ("🔵 Google Gemini Models", "google", "🌐 Cloud • Best embeddings for multilingual content • Excellent Vietnamese/Chinese support"),
            ("🟣 Anthropic Claude Models", "anthropic", "🌐 Cloud • Uses OpenAI embeddings • Best reasoning and analysis"),
            ("🟢 OpenAI GPT Models", "openai", "🌐 Cloud • Good embeddings • Latest reasoning models (o1)"),
            ("🔴 Ollama Local Models", "ollama", "🏠 Local • Complete privacy • No API costs • Requires local setup")
        ]
        
        for provider_title, provider_key, provider_desc in providers:
            # Provider header
            provider_frame = ctk.CTkFrame(scrollable_frame)
            provider_frame.pack(fill="x", pady=(0, 20))
            
            provider_label = ctk.CTkLabel(
                provider_frame,
                text=f"{provider_title}\n{provider_desc}",
                font=ctk.CTkFont(size=14, weight="bold"),
                justify="left"
            )
            provider_label.pack(anchor="w", padx=15, pady=10)
            
            # Models for this provider
            for model in self.MODELS[provider_key]:
                model_frame = ctk.CTkFrame(provider_frame, fg_color="transparent")
                model_frame.pack(fill="x", padx=20, pady=2)
                
                description = self.MODEL_DESCRIPTIONS.get(model, "No description available")
                model_text = f"• {model}\n  {description}"
                
                model_label = ctk.CTkLabel(
                    model_frame,
                    text=model_text,
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    wraplength=800,
                    justify="left",
                    anchor="w"
                )
                model_label.pack(anchor="w", pady=2, fill="x")
        
        # Recommendations
        recommendations_frame = ctk.CTkFrame(scrollable_frame)
        recommendations_frame.pack(fill="x", pady=(10, 0))
        
        rec_title = ctk.CTkLabel(
            recommendations_frame,
            text="💡 Quick Recommendations",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        rec_title.pack(anchor="w", padx=15, pady=(10, 5))
        
        recommendations = [
            "🚀 For Speed: Google gemini-2.0-flash-exp or gemini-1.5-flash",
            "🧠 For Quality: Anthropic claude-4-latest or Google gemini-1.5-pro",
            "🔒 For Privacy: Ollama llama3.1:8b or mixtral:8x7b",
            "💻 For Coding: OpenAI o1-preview or Ollama codellama:13b",
            "💰 For Cost: Google gemini-1.5-flash or OpenAI gpt-4o-mini",
            "🌍 For Multilingual: Google models (best Vietnamese/Chinese embeddings)"
        ]
        
        for rec in recommendations:
            rec_label = ctk.CTkLabel(
                recommendations_frame,
                text=rec,
                font=ctk.CTkFont(size=11),
                text_color="lightblue",
                anchor="w"
            )
            rec_label.pack(anchor="w", padx=30, pady=2, fill="x")
        
        # Close button
        close_button = ctk.CTkButton(
            recommendations_frame,
            text="Close",
            command=info_window.destroy,
            width=100
        )
        close_button.pack(pady=15)
    
    def _create_index_config_section(self):
        """Create the indexing/embeddings configuration section."""
        # Info section
        info_frame = ctk.CTkFrame(self.index_tab)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="🔍 Indexing Configuration\n\n"
            "This model will be used to create embeddings for your documents. "
            "For best multilingual support (Vietnamese, Chinese, etc.), use Google models. "
            "The indexing model affects search quality but not chat responses.",
            font=ctk.CTkFont(size=12),
            wraplength=600,
            justify="left"
        )
        info_text.pack(padx=15, pady=15)
        
        # Provider selection for indexing
        index_provider_label = ctk.CTkLabel(self.index_tab, text="Indexing Provider:")
        index_provider_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.index_provider_var = ctk.StringVar(value="Google Gemini")
        self.index_provider_menu = ctk.CTkOptionMenu(
            self.index_tab,
            values=list(self.PROVIDERS.keys()),
            variable=self.index_provider_var,
            command=self._on_index_provider_change
        )
        self.index_provider_menu.pack(padx=20, pady=5, fill="x")
        
        # Model selection for indexing
        index_model_label = ctk.CTkLabel(self.index_tab, text="Indexing Model:")
        index_model_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.index_model_var = ctk.StringVar(value="gemini-1.5-flash")
        self.index_model_menu = ctk.CTkOptionMenu(
            self.index_tab,
            values=self.MODELS["google"],
            variable=self.index_model_var,
            command=self._on_index_model_change
        )
        self.index_model_menu.pack(padx=20, pady=5, fill="x")
        
        # Index model description
        self.index_desc_label = ctk.CTkLabel(
            self.index_tab,
            text=self.MODEL_DESCRIPTIONS.get("gemini-1.5-flash", ""),
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=600,
            justify="left"
        )
        self.index_desc_label.pack(padx=20, pady=(5, 10), fill="x")
        
    def _create_chat_config_section(self):
        """Create the chat configuration section."""
        # Info section
        info_frame = ctk.CTkFrame(self.chat_tab)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="💬 Chat Configuration\n\n"
            "This model will be used for generating responses in chat. "
            "You can switch chat models anytime in the GUI, but the indexing model is fixed. "
            "Choose based on your preferred balance of speed, quality, and cost.",
            font=ctk.CTkFont(size=12),
            wraplength=600,
            justify="left"
        )
        info_text.pack(padx=15, pady=15)
        
        # Provider selection for chat
        chat_provider_label = ctk.CTkLabel(self.chat_tab, text="Chat Provider:")
        chat_provider_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.chat_provider_var = ctk.StringVar(value="Google Gemini")
        self.chat_provider_menu = ctk.CTkOptionMenu(
            self.chat_tab,
            values=list(self.PROVIDERS.keys()),
            variable=self.chat_provider_var,
            command=self._on_chat_provider_change
        )
        self.chat_provider_menu.pack(padx=20, pady=5, fill="x")
        
        # Model selection for chat
        chat_model_label = ctk.CTkLabel(self.chat_tab, text="Chat Model:")
        chat_model_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.chat_model_var = ctk.StringVar(value="gemini-1.5-flash")
        self.chat_model_menu = ctk.CTkOptionMenu(
            self.chat_tab,
            values=self.MODELS["google"],
            variable=self.chat_model_var,
            command=self._on_chat_model_change
        )
        self.chat_model_menu.pack(padx=20, pady=5, fill="x")
        
        # Chat model description
        self.chat_desc_label = ctk.CTkLabel(
            self.chat_tab,
            text=self.MODEL_DESCRIPTIONS.get("gemini-1.5-flash", ""),
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=600,
            justify="left"
        )
        self.chat_desc_label.pack(padx=20, pady=(5, 10), fill="x")
        
        # Model info button
        info_button = ctk.CTkButton(
            self.chat_tab,
            text="ℹ️ View All Model Details",
            command=self._show_model_info,
            width=200,
            height=35
        )
        info_button.pack(padx=20, pady=10)
        
    def _create_api_keys_section(self):
        """Create the API keys configuration section."""
        # Info section
        info_frame = ctk.CTkFrame(self.api_tab)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="🔑 API Keys Configuration\n\n"
            "Provide API keys for the providers you want to use. You only need keys "
            "for the providers you selected above. Ollama doesn't require an API key.",
            font=ctk.CTkFont(size=12),
            wraplength=600,
            justify="left"
        )
        info_text.pack(padx=15, pady=15)
        
        # API key entries
        self.api_entries = {}
        
        # Google API Key
        google_frame = ctk.CTkFrame(self.api_tab)
        google_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(google_frame, text="Google Gemini API Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(google_frame, text="Get from: https://makersuite.google.com/app/apikey", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=10)
        
        self.google_api_entry = ctk.CTkEntry(google_frame, placeholder_text="Enter Google API key", show="*", width=500)
        self.google_api_entry.pack(padx=10, pady=(5, 10), fill="x")
        self.api_entries["google"] = self.google_api_entry
        
        # Anthropic API Key
        anthropic_frame = ctk.CTkFrame(self.api_tab)
        anthropic_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(anthropic_frame, text="Anthropic Claude API Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(anthropic_frame, text="Get from: https://console.anthropic.com/", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=10)
        
        self.anthropic_api_entry = ctk.CTkEntry(anthropic_frame, placeholder_text="Enter Anthropic API key", show="*", width=500)
        self.anthropic_api_entry.pack(padx=10, pady=(5, 10), fill="x")
        self.api_entries["anthropic"] = self.anthropic_api_entry
        
        # OpenAI API Key
        openai_frame = ctk.CTkFrame(self.api_tab)
        openai_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(openai_frame, text="OpenAI GPT API Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(openai_frame, text="Get from: https://platform.openai.com/api-keys", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=10)
        
        self.openai_api_entry = ctk.CTkEntry(openai_frame, placeholder_text="Enter OpenAI API key", show="*", width=500)
        self.openai_api_entry.pack(padx=10, pady=(5, 10), fill="x")
        self.api_entries["openai"] = self.openai_api_entry
        
        # Ollama URL
        ollama_frame = ctk.CTkFrame(self.api_tab)
        ollama_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(ollama_frame, text="Ollama Base URL (optional):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(ollama_frame, text="Default: http://localhost:11434", font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=10)
        
        self.ollama_entry = ctk.CTkEntry(ollama_frame, placeholder_text="http://localhost:11434", width=500)
        self.ollama_entry.pack(padx=10, pady=(5, 10), fill="x")
    
    def _on_index_provider_change(self, choice):
        """Handle indexing provider selection change."""
        provider_key = self.PROVIDERS[choice]
        models = self.MODELS[provider_key]
        self.index_model_menu.configure(values=models)
        self.index_model_var.set(models[0])
        self._update_index_model_description(models[0])
        
    def _on_index_model_change(self, choice):
        """Handle indexing model selection change."""
        self._update_index_model_description(choice)
        
    def _update_index_model_description(self, model):
        """Update the indexing model description."""
        description = self.MODEL_DESCRIPTIONS.get(model, "Model description not available")
        self.index_desc_label.configure(text=description)
        
    def _on_chat_provider_change(self, choice):
        """Handle chat provider selection change."""
        provider_key = self.PROVIDERS[choice]
        models = self.MODELS[provider_key]
        self.chat_model_menu.configure(values=models)
        self.chat_model_var.set(models[0])
        self._update_chat_model_description(models[0])
        
    def _on_chat_model_change(self, choice):
        """Handle chat model selection change."""
        self._update_chat_model_description(choice)
        
    def _update_chat_model_description(self, model):
        """Update the chat model description."""
        description = self.MODEL_DESCRIPTIONS.get(model, "Model description not available")
        self.chat_desc_label.configure(text=description)
        
    def _on_provider_change(self, choice):
        """Handle provider selection change."""
        provider_key = self.PROVIDERS[choice]
        models = self.MODELS[provider_key]
        self.model_menu.configure(values=models)
        self.model_var.set(models[0])
        
        # Update model description for first model
        description = self.MODEL_DESCRIPTIONS.get(models[0], "Model description not available")
        self.model_desc_label.configure(text=description)
        
        # Show/hide Ollama-specific fields
        if provider_key == "ollama":
            # Show Ollama fields
            self.ollama_label.pack(anchor="w", padx=30, pady=(10, 0))
            self.ollama_entry.pack(padx=30, pady=5, fill="x")
            
            # Update API key field for Ollama
            self.api_label.configure(text="API Key (optional for Ollama):")
            self.api_entry.configure(placeholder_text="Optional: API key for secured Ollama instances")
            self.api_entry.configure(show="")  # Don't hide text for optional field
            
            # Check if custom model is selected
            if self.model_var.get() == "custom-model":
                self.custom_model_label.pack(anchor="w", padx=30, pady=(10, 0))
                self.custom_model_entry.pack(padx=30, pady=5, fill="x")
        else:
            # Hide Ollama fields
            self.ollama_label.pack_forget()
            self.ollama_entry.pack_forget()
            self.custom_model_label.pack_forget()
            self.custom_model_entry.pack_forget()
            
            # Reset API key field for cloud providers
            self.api_label.configure(text="API Key:")
            self.api_entry.configure(placeholder_text="Paste your API key here")
            self.api_entry.configure(show="*")  # Hide API key text
            
        # Handle custom model selection
        if self.model_var.get() == "custom-model" and provider_key == "ollama":
            self.custom_model_label.pack(anchor="w", padx=30, pady=(10, 0))
            self.custom_model_entry.pack(padx=30, pady=5, fill="x")
        
        # Update model description and handle custom models
        self._on_model_change(models[0])
        
    def _on_model_change(self, choice):
        """Handle model selection change."""
        provider_key = self.PROVIDERS[self.provider_var.get()]
        
        # Update model description
        description = self.MODEL_DESCRIPTIONS.get(choice, "Model description not available")
        self.model_desc_label.configure(text=description)
        
        if provider_key == "ollama" and choice == "custom-model":
            self.custom_model_label.pack(anchor="w", padx=30, pady=(10, 0))
            self.custom_model_entry.pack(padx=30, pady=5, fill="x")
        else:
            self.custom_model_label.pack_forget()
            self.custom_model_entry.pack_forget()
        
    def _check_and_install_tesseract(self, language_code: str) -> bool:
        """Check and install Tesseract language support if needed."""
        try:
            # Check if tesseract is installed
            result = subprocess.run(['tesseract', '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.status_label.configure(
                    text="Tesseract OCR not found. Please install it first.",
                    text_color="red"
                )
                return False
                
            # Check if language is already supported
            lang_result = subprocess.run(['tesseract', '--list-langs'], 
                                       capture_output=True, text=True, timeout=10)
            
            if language_code in lang_result.stdout:
                return True  # Language already available
                
            # Try to install language pack based on OS
            os_name = platform.system().lower()
            
            if os_name == "darwin":  # macOS
                self.status_label.configure(
                    text="Installing Vietnamese language support for OCR...",
                    text_color="blue"
                )
                subprocess.run(['brew', 'install', 'tesseract-lang'], 
                             check=True, timeout=60)
                             
            elif os_name == "linux":
                # Try different package managers
                if shutil.which('apt-get'):
                    self.status_label.configure(
                        text="Installing Vietnamese language support for OCR...",
                        text_color="blue"
                    )
                    if language_code == "vie":
                        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tesseract-ocr-vie'], 
                                     check=True, timeout=60)
                    elif language_code == "chi_sim":
                        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tesseract-ocr-chi-sim'], 
                                     check=True, timeout=60)
                    elif language_code == "chi_tra":
                        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tesseract-ocr-chi-tra'], 
                                     check=True, timeout=60)
                    elif language_code == "jpn":
                        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'tesseract-ocr-jpn'], 
                                     check=True, timeout=60)
                        
            # Verify installation worked
            verify_result = subprocess.run(['tesseract', '--list-langs'], 
                                         capture_output=True, text=True, timeout=10)
            if language_code not in verify_result.stdout:
                self.status_label.configure(
                    text=f"Could not install {language_code} language pack. Please install manually.",
                    text_color="orange"
                )
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            self.status_label.configure(
                text="Tesseract installation timed out. Please install language packs manually.",
                text_color="orange"
            )
            return False
        except subprocess.CalledProcessError as e:
            self.status_label.configure(
                text=f"Could not install language pack: {str(e)}. Please install manually.",
                text_color="orange"
            )
            return False
        except Exception as e:
            self.status_label.configure(
                text=f"Error checking Tesseract: {str(e)}",
                text_color="orange"
            )
            return False
    
    def _on_initialize(self):
        """Handle initialization button click."""
        # Get indexing configuration
        index_provider_key = self.PROVIDERS[self.index_provider_var.get()]
        index_model = self.index_model_var.get()
        
        # Get chat configuration  
        chat_provider_key = self.PROVIDERS[self.chat_provider_var.get()]
        chat_model = self.chat_model_var.get()
        
        # Get language code early for Tesseract check
        language_code = self.LANGUAGES[self.lang_var.get()]
        
        # Collect API keys
        api_keys = {}
        required_providers = {index_provider_key, chat_provider_key}
        
        for provider in required_providers:
            if provider != "ollama":  # Ollama doesn't need API key
                if provider in self.api_entries:
                    key = self.api_entries[provider].get().strip()
                    if not key:
                        self.status_label.configure(
                            text=f"Please enter an API key for {provider.title()}",
                            text_color="red"
                        )
                        return
                    api_keys[provider] = key
        
        # Validate that at least one API key is provided for non-Ollama setups
        if not api_keys and "ollama" not in required_providers:
            self.status_label.configure(
                text="Please provide at least one API key",
                text_color="red"
            )
            return
            
        # Final status update
        self.status_label.configure(
            text="Creating configuration...",
            text_color="blue"
        )
        self.root.update()
            
        # Check and install Tesseract language support if needed
        if language_code != "eng":  # Only check for non-English languages
            self.status_label.configure(
                text="Checking OCR language support...",
                text_color="blue"
            )
            self.root.update()  # Update UI
            
            tesseract_ok = self._check_and_install_tesseract(language_code)
            if not tesseract_ok and language_code in ["vie", "chi_sim", "chi_tra", "jpn"]:
                # Show warning but don't block setup for important languages
                self.status_label.configure(
                    text=f"Warning: {language_code} OCR may not work optimally. Continuing setup...",
                    text_color="orange"
                )
                self.root.update()
                self.root.after(2000)  # Show warning for 2 seconds
        
        # Get Ollama URL if applicable
        ollama_url = None
        if "ollama" in required_providers:
            ollama_url = self.ollama_entry.get().strip()
            if not ollama_url:
                ollama_url = "http://localhost:11434"  # Default
        
        # Create configuration with separate index and chat settings
        from pydantic import SecretStr
        
        # Use the first provided API key as the primary key for backwards compatibility
        primary_key = list(api_keys.values())[0] if api_keys else "not-required"
        primary_provider = index_provider_key  # Use index provider as primary
        
        self.result = SageConfig(
            project_path=self.project_path,
            # Backwards compatibility fields
            api_key=SecretStr(primary_key),
            llm_provider=primary_provider,
            llm_model=index_model,
            # New separate configuration
            index_provider=index_provider_key,
            index_model=index_model,
            chat_provider=chat_provider_key,
            chat_model=chat_model,
            # API keys
            google_api_key=SecretStr(api_keys.get("google", "")) if api_keys.get("google") else None,
            anthropic_api_key=SecretStr(api_keys.get("anthropic", "")) if api_keys.get("anthropic") else None,
            openai_api_key=SecretStr(api_keys.get("openai", "")) if api_keys.get("openai") else None,
            # Other settings
            document_language=language_code,
            ollama_url=ollama_url
        )
        
        # Save configuration
        try:
            self.config_manager.save(self.result)
            self.status_label.configure(
                text="Configuration saved successfully!\n"
                f"Indexing: {index_provider_key.title()} {index_model}\n"
                f"Chat: {chat_provider_key.title()} {chat_model}",
                text_color="green"
            )
            self.root.after(2000, self.root.quit)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.configure(
                text=f"Error: {str(e)}",
                text_color="red"
            )
            
    def _on_cancel(self):
        """Handle cancel button click."""
        self.root.quit()
        
    def run(self) -> Optional[SageConfig]:
        """Run the GUI and return the configuration."""
        self.root.mainloop()
        self.root.destroy()
        return self.result