"""GUI setup window for Project Sage initialization."""

import customtkinter as ctk
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
    
    MODELS = {
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
            "claude-4-latest",  # Future Claude 4
            "claude-4-preview"  # Future Claude 4 preview
        ],
        "openai": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview", 
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5-preview",  # Future GPT-5
            "gpt-5-turbo",    # Future GPT-5 turbo
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
        self.root.title("Project Sage Setup")
        self.root.geometry("600x550")
        self.root.resizable(False, False)
        
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
        
        # Provider selection
        provider_label = ctk.CTkLabel(self.root, text="LLM Provider:")
        provider_label.pack(anchor="w", padx=30, pady=(10, 0))
        
        self.provider_var = ctk.StringVar(value="Google Gemini")
        self.provider_menu = ctk.CTkOptionMenu(
            self.root,
            values=list(self.PROVIDERS.keys()),
            variable=self.provider_var,
            command=self._on_provider_change
        )
        self.provider_menu.pack(padx=30, pady=5, fill="x")
        
        # Model selection
        model_label = ctk.CTkLabel(self.root, text="Model:")
        model_label.pack(anchor="w", padx=30, pady=(10, 0))
        
        self.model_var = ctk.StringVar(value="gemini-1.5-flash")
        self.model_menu = ctk.CTkOptionMenu(
            self.root,
            values=self.MODELS["google"],
            variable=self.model_var
        )
        self.model_menu.pack(padx=30, pady=5, fill="x")
        
        # API key input (conditional)
        self.api_label = ctk.CTkLabel(self.root, text="API Key:")
        self.api_label.pack(anchor="w", padx=30, pady=(10, 0))
        
        self.api_entry = ctk.CTkEntry(
            self.root, 
            placeholder_text="Paste your API key here (not needed for Ollama)",
            show="*"
        )
        self.api_entry.pack(padx=30, pady=5, fill="x")
        
        # Ollama URL input (initially hidden)
        self.ollama_label = ctk.CTkLabel(self.root, text="Ollama Base URL:")
        self.ollama_entry = ctk.CTkEntry(
            self.root,
            placeholder_text="http://localhost:11434 (default)"
        )
        
        # Custom model input (initially hidden)
        self.custom_model_label = ctk.CTkLabel(self.root, text="Custom Model Name:")
        self.custom_model_entry = ctk.CTkEntry(
            self.root,
            placeholder_text="Enter custom model name (e.g., my-model:latest)"
        )
        
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
        
    def _on_provider_change(self, choice):
        """Handle provider selection change."""
        provider_key = self.PROVIDERS[choice]
        models = self.MODELS[provider_key]
        self.model_menu.configure(values=models)
        self.model_var.set(models[0])
        
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
        
        # Bind model selection change for custom model handling
        self.model_menu.configure(command=self._on_model_change)
        
    def _on_model_change(self, choice):
        """Handle model selection change."""
        provider_key = self.PROVIDERS[self.provider_var.get()]
        
        if provider_key == "ollama" and choice == "custom-model":
            self.custom_model_label.pack(anchor="w", padx=30, pady=(10, 0))
            self.custom_model_entry.pack(padx=30, pady=5, fill="x")
        else:
            self.custom_model_label.pack_forget()
            self.custom_model_entry.pack_forget()
        
    def _on_initialize(self):
        """Handle initialization button click."""
        provider_key = self.PROVIDERS[self.provider_var.get()]
        api_key = self.api_entry.get().strip()
        
        # Validate inputs based on provider
        if provider_key != "ollama" and not api_key:
            self.status_label.configure(
                text="Please enter an API key",
                text_color="red"
            )
            return
            
        # Get model name (handle custom models)
        selected_model = self.model_var.get()
        if selected_model == "custom-model" and provider_key == "ollama":
            custom_model = self.custom_model_entry.get().strip()
            if not custom_model:
                self.status_label.configure(
                    text="Please enter a custom model name",
                    text_color="red"
                )
                return
            selected_model = custom_model
            
        # Create configuration
        language_code = self.LANGUAGES[self.lang_var.get()]
        
        # Get Ollama URL if applicable
        ollama_url = None
        if provider_key == "ollama":
            ollama_url = self.ollama_entry.get().strip()
            if not ollama_url:
                ollama_url = "http://localhost:11434"  # Default
        
        self.result = SageConfig(
            project_path=self.project_path,
            api_key=api_key if api_key else "not-required",  # Handle empty API key for Ollama
            llm_provider=provider_key,
            llm_model=selected_model,
            document_language=language_code,
            ollama_url=ollama_url if provider_key == "ollama" else None
        )
        
        # Save configuration
        try:
            self.config_manager.save(self.result)
            self.status_label.configure(
                text="Configuration saved successfully!",
                text_color="green"
            )
            self.root.after(1000, self.root.quit)
        except Exception as e:
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