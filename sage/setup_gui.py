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
        "OpenAI GPT": "openai"
    }
    
    MODELS = {
        "google": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
        "anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
        "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
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
        
        # API key input
        api_label = ctk.CTkLabel(self.root, text="API Key:")
        api_label.pack(anchor="w", padx=30, pady=(10, 0))
        
        self.api_entry = ctk.CTkEntry(
            self.root, 
            placeholder_text="Paste your API key here",
            show="*"
        )
        self.api_entry.pack(padx=30, pady=5, fill="x")
        
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
        
    def _on_initialize(self):
        """Handle initialization button click."""
        api_key = self.api_entry.get().strip()
        
        if not api_key:
            self.status_label.configure(
                text="Please enter an API key",
                text_color="red"
            )
            return
            
        # Create configuration
        provider_key = self.PROVIDERS[self.provider_var.get()]
        language_code = self.LANGUAGES[self.lang_var.get()]
        
        self.result = SageConfig(
            project_path=self.project_path,
            api_key=api_key,
            llm_provider=provider_key,
            llm_model=self.model_var.get(),
            document_language=language_code
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