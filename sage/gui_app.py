"""Enhanced GUI application for Project Sage with file browser and vector viewer."""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import json
import os
import subprocess
import platform
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkinter
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from sage.config import ConfigManager, SageConfig
from sage.file_processor import FileProcessor
from sage.vector_store import VectorStore
from sage.llm_client import LLMClient
from sage.model_manager import ModelManager


class SageGUI:
    """Enhanced GUI for Project Sage with file browser and vector visualization."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.config_manager = ConfigManager(project_path)
        self.config = self.config_manager.load()
        
        # Set appearance
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title(f"Project Sage - {project_path.name}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Initialize components if configured
        self.file_processor = None
        self.vector_store = None
        self.llm_client = None
        self.model_manager = None
        if self.config:
            self.file_processor = FileProcessor(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                ocr_language=self.config.document_language
            )
            self.vector_store = VectorStore(self.config)
            self.vector_store.initialize()
            self.llm_client = LLMClient(self.config)
            self.model_manager = ModelManager(self.config)
            
        self._create_widgets()
        self._load_data()
        
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.overview_tab = self.notebook.add("Overview")
        self.files_tab = self.notebook.add("Files")
        self.vectors_tab = self.notebook.add("Vectors")
        self.chat_tab = self.notebook.add("Chat")
        self.config_tab = self.notebook.add("Config")
        
        self._create_overview_tab()
        self._create_files_tab()
        self._create_vectors_tab()
        self._create_chat_tab()
        self._create_config_tab()
        
    def _create_overview_tab(self):
        """Create the overview tab."""
        # Project info frame
        info_frame = ctk.CTkFrame(self.overview_tab)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame, 
            text="Project Information",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Stats grid
        stats_frame = ctk.CTkFrame(info_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_labels = {}
        # Get model information 
        chat_model_info = "Not configured"
        index_model_info = "Not configured"
        if self.config:
            if self.model_manager:
                chat_provider, chat_model = self.model_manager.get_current_model_info()
                chat_model_info = f"{chat_provider.title()} {chat_model}"
            
            index_provider, index_model = self.config.get_index_provider_model()
            index_model_info = f"{index_provider.title()} {index_model}"
        
        stats = [
            ("Project Path", str(self.project_path)),
            ("Configuration", "Loaded" if self.config else "Not configured"),
            ("💬 Chat Model", chat_model_info),
            ("📚 Index Model", index_model_info), 
            ("Files Indexed", "0"),
            ("Total Chunks", "0"),
            ("Last Update", "Never")
        ]
        
        for i, (label, value) in enumerate(stats):
            ctk.CTkLabel(stats_frame, text=f"{label}:", font=ctk.CTkFont(weight="bold")).grid(
                row=i, column=0, sticky="w", padx=10, pady=5
            )
            label_widget = ctk.CTkLabel(stats_frame, text=value)
            label_widget.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            self.stats_labels[label] = label_widget
            
        # Action buttons
        buttons_frame = ctk.CTkFrame(self.overview_tab)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            buttons_frame, 
            text="Actions",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))
        
        button_container = ctk.CTkFrame(buttons_frame)
        button_container.pack(pady=10)
        
        ctk.CTkButton(
            button_container,
            text="Update Index",
            command=self._update_index,
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_container,
            text="Force Reindex",
            command=lambda: self._update_index(force=True),
            width=150
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_container,
            text="Refresh Data",
            command=self._load_data,
            width=150
        ).pack(side="left", padx=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.overview_tab,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=10)
        
    def _create_files_tab(self):
        """Create the files tab with indexed files list."""
        # Search frame
        search_frame = ctk.CTkFrame(self.files_tab)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(search_frame, text="Search Files:").pack(side="left", padx=10)
        self.file_search = ctk.CTkEntry(search_frame, placeholder_text="Enter filename or path...")
        self.file_search.pack(side="left", fill="x", expand=True, padx=10)
        self.file_search.bind("<KeyRelease>", self._filter_files)
        
        # Files list frame
        files_frame = ctk.CTkFrame(self.files_tab)
        files_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create treeview for files
        columns = ("File", "Type", "Chunks", "Last Modified", "Status")
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.files_tree.heading("#0", text="Path")
        self.files_tree.column("#0", width=300)
        
        for col in columns:
            self.files_tree.heading(col, text=col)
            if col == "File":
                self.files_tree.column(col, width=200)
            elif col == "Type":
                self.files_tree.column(col, width=80)
            elif col == "Chunks":
                self.files_tree.column(col, width=80)
            elif col == "Last Modified":
                self.files_tree.column(col, width=150)
            else:
                self.files_tree.column(col, width=100)
                
        # Scrollbars
        v_scroll = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        h_scroll = ttk.Scrollbar(files_frame, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack treeview and scrollbars
        self.files_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        
        # Bind selection and double-click
        self.files_tree.bind("<<TreeviewSelect>>", self._on_file_select)
        self.files_tree.bind("<Double-1>", self._on_file_double_click)
        self.files_tree.bind("<Button-2>", self._on_file_right_click)  # Right click (Mac)
        self.files_tree.bind("<Button-3>", self._on_file_right_click)  # Right click (Windows/Linux)
        
        # Instructions frame
        instructions_frame = ctk.CTkFrame(self.files_tab)
        instructions_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        instructions_text = "💡 Double-click files to open them | Right-click for more options"
        ctk.CTkLabel(
            instructions_frame, 
            text=instructions_text,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=5)
        
        # File details frame
        details_frame = ctk.CTkFrame(self.files_tab)
        details_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            details_frame, 
            text="File Details",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.file_details = ctk.CTkTextbox(details_frame, height=100)
        self.file_details.pack(fill="x", padx=10, pady=5)
        
    def _create_vectors_tab(self):
        """Create the vectors tab with vector database information."""
        # Vector stats frame
        stats_frame = ctk.CTkFrame(self.vectors_tab)
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            stats_frame, 
            text="Vector Database Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.vector_stats = ctk.CTkTextbox(stats_frame, height=100)
        self.vector_stats.pack(fill="x", padx=10, pady=5)
        
        # Sample vectors frame
        samples_frame = ctk.CTkFrame(self.vectors_tab)
        samples_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            samples_frame, 
            text="Sample Document Chunks",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        # Create treeview for vectors
        vector_columns = ("ID", "Source", "Chunk", "Content Preview")
        self.vectors_tree = ttk.Treeview(samples_frame, columns=vector_columns, show="headings")
        
        for col in vector_columns:
            self.vectors_tree.heading(col, text=col)
            if col == "ID":
                self.vectors_tree.column(col, width=100)
            elif col == "Source":
                self.vectors_tree.column(col, width=200)
            elif col == "Chunk":
                self.vectors_tree.column(col, width=80)
            else:
                self.vectors_tree.column(col, width=400)
                
        # Scrollbar for vectors
        v_scroll2 = ttk.Scrollbar(samples_frame, orient="vertical", command=self.vectors_tree.yview)
        self.vectors_tree.configure(yscrollcommand=v_scroll2.set)
        
        self.vectors_tree.pack(side="left", fill="both", expand=True)
        v_scroll2.pack(side="right", fill="y")
        
        # Vector details
        self.vectors_tree.bind("<<TreeviewSelect>>", self._on_vector_select)
        
        vector_details_frame = ctk.CTkFrame(self.vectors_tab)
        vector_details_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            vector_details_frame, 
            text="Vector Details",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.vector_details = ctk.CTkTextbox(vector_details_frame, height=150)
        self.vector_details.pack(fill="x", padx=10, pady=5)
        
    def _create_chat_tab(self):
        """Create the chat tab for interactive conversation."""
        if not self.config or not self.model_manager:
            ctk.CTkLabel(
                self.chat_tab,
                text="Project not configured. Please run 'sage setup' first.",
                font=ctk.CTkFont(size=16)
            ).pack(expand=True)
            return
        
        # Model selection frame at top
        model_frame = ctk.CTkFrame(self.chat_tab)
        model_frame.pack(fill="x", padx=10, pady=10)
        
        # Current model display and controls
        model_header = ctk.CTkFrame(model_frame)
        model_header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            model_header,
            text="🤖 Current Model",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Model selector controls
        model_controls = ctk.CTkFrame(model_header)
        model_controls.pack(side="right")
        
        # Provider selection - show all providers, indicate availability
        all_providers = list(self.model_manager.get_available_models().keys())
        configured_providers = self.model_manager.get_configured_providers()
        
        # Create provider display names with availability indicators
        provider_display_names = []
        provider_name_map = {}  # Maps display name back to actual provider name
        
        for provider in all_providers:
            if provider in configured_providers:
                display_name = f"✅ {provider.title()}"
            else:
                display_name = f"❌ {provider.title()} (No API Key)"
            provider_display_names.append(display_name)
            provider_name_map[display_name] = provider
        
        current_provider, current_model = self.model_manager.get_current_model_info()
        current_display = f"✅ {current_provider.title()}" if current_provider in configured_providers else f"❌ {current_provider.title()} (No API Key)"
        
        self.chat_provider_var = ctk.StringVar(value=current_display)
        self.chat_provider_name_map = provider_name_map  # Store for lookup
        self.chat_provider_menu = ctk.CTkOptionMenu(
            model_controls,
            values=provider_display_names,
            variable=self.chat_provider_var,
            command=self._on_chat_provider_change,
            width=200
        )
        self.chat_provider_menu.pack(side="left", padx=5)
        
        # Model selection
        available_models = self.model_manager.get_available_models()[current_provider]
        self.chat_model_var = ctk.StringVar(value=current_model)
        self.chat_model_menu = ctk.CTkOptionMenu(
            model_controls,
            values=available_models,
            variable=self.chat_model_var,
            command=self._on_chat_model_change,
            width=200
        )
        self.chat_model_menu.pack(side="left", padx=5)
        
        # Model info button
        info_button = ctk.CTkButton(
            model_controls,
            text="ℹ️",
            width=30,
            command=self._show_model_recommendations,
        )
        info_button.pack(side="left", padx=5)
        
        # Add API key button
        api_button = ctk.CTkButton(
            model_controls,
            text="🔑 API Keys",
            width=80,
            command=self._manage_api_keys,
        )
        api_button.pack(side="left", padx=5)
        
        # Current model status
        self.model_status_label = ctk.CTkLabel(
            model_frame,
            text=self._get_current_model_status(),
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.model_status_label.pack(padx=10, pady=(0, 10))
        
        # Chat conversation area
        chat_frame = ctk.CTkFrame(self.chat_tab)
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Chat history
        self.chat_history = ctk.CTkScrollableFrame(chat_frame)
        self.chat_history.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Input area at bottom
        input_frame = ctk.CTkFrame(self.chat_tab)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # Message input
        message_container = ctk.CTkFrame(input_frame)
        message_container.pack(fill="x", padx=10, pady=10)
        
        self.chat_entry = ctk.CTkEntry(
            message_container,
            placeholder_text="Ask a question about your project documents...",
            height=40
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.chat_entry.bind("<Return>", self._send_chat_message)
        
        self.chat_send_button = ctk.CTkButton(
            message_container,
            text="Send",
            command=self._send_chat_message,
            width=80,
            height=40
        )
        self.chat_send_button.pack(side="right", padx=5)
        
        # Chat controls
        controls_frame = ctk.CTkFrame(input_frame)
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.clear_chat_button = ctk.CTkButton(
            controls_frame,
            text="Clear Chat",
            command=self._clear_chat_history,
            width=100,
            height=30,
            fg_color="gray"
        )
        self.clear_chat_button.pack(side="left", padx=5)
        
        self.save_chat_button = ctk.CTkButton(
            controls_frame,
            text="Save Chat",
            command=self._save_chat_history,
            width=100,
            height=30
        )
        self.save_chat_button.pack(side="left", padx=5)
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Add welcome message
        self._add_chat_message("🤖 Sage", 
            f"Hello! I'm ready to help you with questions about your project.\n\n"
            f"📚 Knowledge base: {self.vector_store.get_document_count() if self.vector_store else 0} document chunks indexed\n"
            f"🤖 Current model: {current_provider.title()} {current_model}\n\n"
            f"Ask me anything about your documents!", 
            is_bot=True)
        
    def _create_config_tab(self):
        """Create the configuration tab."""
        if not self.config:
            ctk.CTkLabel(
                self.config_tab,
                text="Project not configured. Please run 'sage setup' first.",
                font=ctk.CTkFont(size=16)
            ).pack(expand=True)
            return
            
        # Config display
        config_frame = ctk.CTkFrame(self.config_tab)
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            config_frame, 
            text="Current Configuration",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=10)
        
        # Get separate index and chat configurations
        index_provider, index_model = self.config.get_index_provider_model()
        chat_provider, chat_model = self.config.get_chat_provider_model()
        
        # Show both legacy and new dual model configuration
        config_data = {
            "Project Path": str(self.config.project_path),
            "📚 Index Provider": index_provider.title(),
            "📚 Index Model": index_model,
            "💬 Chat Provider": chat_provider.title(), 
            "💬 Chat Model": chat_model,
            "Document Language": self.config.document_language,
            "Embedding Model": self.config.embedding_model,
            "Chunk Size": str(self.config.chunk_size),
            "Chunk Overlap": str(self.config.chunk_overlap)
        }
        
        # Add legacy info if different from dual model setup
        if (index_provider != self.config.llm_provider or 
            index_model != self.config.llm_model):
            config_data["⚠️ Legacy Provider"] = self.config.llm_provider.title()
            config_data["⚠️ Legacy Model"] = self.config.llm_model
        
        for key, value in config_data.items():
            row_frame = ctk.CTkFrame(config_frame)
            row_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                row_frame, 
                text=f"{key}:",
                font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=10)
            
            ctk.CTkLabel(row_frame, text=value).pack(side="left", padx=10)
            
    def _load_data(self):
        """Load and refresh all data displays."""
        if not self.config or not self.file_processor:
            return
            
        # Load file metadata
        metadata = self.file_processor.load_metadata(self.project_path)
        
        # Update overview stats
        self.stats_labels["Files Indexed"].configure(text=str(len(metadata)))
        
        if self.vector_store:
            doc_count = self.vector_store.get_document_count()
            self.stats_labels["Total Chunks"].configure(text=str(doc_count))
        else:
            self.stats_labels["Total Chunks"].configure(text="0")
            
        if metadata:
            last_update = max(
                datetime.fromisoformat(m['processed_at']) 
                for m in metadata.values()
            )
            self.stats_labels["Last Update"].configure(
                text=last_update.strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            self.stats_labels["Last Update"].configure(text="Never")
            
        # Load files data
        self._load_files_data(metadata)
        
        # Load vector data
        self._load_vector_data()
        
    def _load_files_data(self, metadata):
        """Load files data into the tree view."""
        # Clear existing data
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        # Add files to tree
        for file_path, file_meta in metadata.items():
            rel_path = Path(file_path).relative_to(self.project_path)
            file_name = Path(file_path).name
            file_type = Path(file_path).suffix.upper()
            chunks = str(file_meta.get('chunk_count', 0))
            last_mod = file_meta.get('processed_at', 'Unknown')
            if last_mod != 'Unknown':
                try:
                    dt = datetime.fromisoformat(last_mod)
                    last_mod = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
                    
            status = "Indexed"
            
            self.files_tree.insert(
                "", "end",
                text=str(rel_path),
                values=(file_name, file_type, chunks, last_mod, status)
            )
            
    def _load_vector_data(self):
        """Load vector database samples."""
        if not self.vector_store:
            return
            
        # Clear existing data
        for item in self.vectors_tree.get_children():
            self.vectors_tree.delete(item)
            
        # Update vector stats
        doc_count = self.vector_store.get_document_count()
        stats_text = f"Total Documents: {doc_count}\n"
        stats_text += f"Embedding Model: {self.config.embedding_model}\n"
        stats_text += f"Vector Database: ChromaDB (Local)\n"
        stats_text += f"Database Path: {self.config_manager.get_db_path()}"
        
        self.vector_stats.delete("1.0", "end")
        self.vector_stats.insert("1.0", stats_text)
        
        # Get sample documents from vector store
        try:
            if doc_count > 0:
                # Try to get some sample documents
                sample_docs = self.vector_store.search("example", k=min(20, doc_count))
                
                for i, doc in enumerate(sample_docs):
                    source = doc.metadata.get('source', 'Unknown')
                    rel_source = str(Path(source).relative_to(self.project_path)) if source != 'Unknown' else 'Unknown'
                    chunk_idx = doc.metadata.get('chunk_index', 0)
                    content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    
                    self.vectors_tree.insert(
                        "", "end",
                        values=(f"chunk_{i}", rel_source, str(chunk_idx + 1), content_preview)
                    )
        except Exception as e:
            print(f"Error loading vector samples: {e}")
            
    def _filter_files(self, event):
        """Filter files based on search term."""
        search_term = self.file_search.get().lower()
        
        # Clear and reload with filter
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        if not self.file_processor:
            return
            
        metadata = self.file_processor.load_metadata(self.project_path)
        
        for file_path, file_meta in metadata.items():
            if search_term in file_path.lower():
                rel_path = Path(file_path).relative_to(self.project_path)
                file_name = Path(file_path).name
                file_type = Path(file_path).suffix.upper()
                chunks = str(file_meta.get('chunk_count', 0))
                last_mod = file_meta.get('processed_at', 'Unknown')
                if last_mod != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(last_mod)
                        last_mod = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                        
                status = "Indexed"
                
                self.files_tree.insert(
                    "", "end",
                    text=str(rel_path),
                    values=(file_name, file_type, chunks, last_mod, status)
                )
                
    def _on_file_select(self, event):
        """Handle file selection in tree view."""
        selection = self.files_tree.selection()
        if not selection:
            return
            
        item = self.files_tree.item(selection[0])
        file_path = item['text']
        file_name = item['values'][0]
        
        # Show file details
        details = f"File: {file_name}\n"
        details += f"Path: {file_path}\n"
        details += f"Type: {item['values'][1]}\n"
        details += f"Chunks: {item['values'][2]}\n"
        details += f"Last Modified: {item['values'][3]}\n"
        details += f"Status: {item['values'][4]}\n"
        
        # Try to get actual file info
        try:
            full_path = self.project_path / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                details += f"Size: {size:,} bytes\n"
        except:
            pass
            
        self.file_details.delete("1.0", "end")
        self.file_details.insert("1.0", details)
        
    def _on_file_double_click(self, event):
        """Handle double-click on file to open it."""
        selection = self.files_tree.selection()
        if not selection:
            return
            
        item = self.files_tree.item(selection[0])
        file_path = item['text']
        full_path = self.project_path / file_path
        
        self._open_file(full_path)
        
    def _on_file_right_click(self, event):
        """Handle right-click on file to show context menu."""
        # Select the item under cursor
        item_id = self.files_tree.identify_row(event.y)
        if not item_id:
            return
            
        self.files_tree.selection_set(item_id)
        item = self.files_tree.item(item_id)
        file_path = item['text']
        full_path = self.project_path / file_path
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(
            label="📂 Open File", 
            command=lambda: self._open_file(full_path)
        )
        context_menu.add_command(
            label="📁 Show in Finder/Explorer", 
            command=lambda: self._show_in_explorer(full_path)
        )
        context_menu.add_command(
            label="📋 Copy Path", 
            command=lambda: self._copy_path_to_clipboard(str(full_path))
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="🔄 Reindex This File", 
            command=lambda: self._reindex_single_file(full_path)
        )
        
        # Show context menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def _open_file(self, file_path: Path):
        """Open file with default application."""
        if not file_path.exists():
            messagebox.showerror("Error", f"File not found: {file_path}")
            return
            
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(file_path)], check=True)
            elif platform.system() == "Windows":  # Windows
                os.startfile(str(file_path))
            else:  # Linux and other Unix-like
                subprocess.run(["xdg-open", str(file_path)], check=True)
                
            self._show_status(f"📂 Opened: {file_path.name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
            
    def _show_in_explorer(self, file_path: Path):
        """Show file in system file explorer."""
        if not file_path.exists():
            messagebox.showerror("Error", f"File not found: {file_path}")
            return
            
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(file_path)], check=True)
            elif platform.system() == "Windows":  # Windows
                subprocess.run(["explorer", "/select,", str(file_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(file_path.parent)], check=True)
                
            self._show_status(f"📁 Showed in explorer: {file_path.name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not show in explorer: {str(e)}")
            
    def _copy_path_to_clipboard(self, path: str):
        """Copy file path to clipboard."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(path)
            self._show_status(f"📋 Copied to clipboard: {Path(path).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy to clipboard: {str(e)}")
            
    def _reindex_single_file(self, file_path: Path):
        """Reindex a single file."""
        if not self.config or not self.file_processor or not self.vector_store:
            messagebox.showerror("Error", "Project not configured properly.")
            return
            
        def reindex_thread():
            try:
                self.root.after(0, lambda: self._show_status(f"🔄 Reindexing {file_path.name}..."))
                
                # Process the file
                documents = self.file_processor.process_file(file_path)
                if documents:
                    # Remove old chunks for this file first (simplified approach)
                    self.vector_store.add_documents(documents)
                    self.file_processor.update_metadata(self.project_path, file_path, documents)
                    
                    status = f"✅ Reindexed {file_path.name} - {len(documents)} chunks"
                    self.root.after(0, lambda: self._show_status(status))
                    self.root.after(0, self._load_data)
                else:
                    self.root.after(0, lambda: self._show_status(f"❌ Failed to reindex {file_path.name}"))
                    
            except Exception as e:
                error_msg = f"❌ Error reindexing {file_path.name}: {str(e)}"
                self.root.after(0, lambda: self._show_status(error_msg))
                
        threading.Thread(target=reindex_thread, daemon=True).start()
        
    def _on_vector_select(self, event):
        """Handle vector selection in tree view."""
        selection = self.vectors_tree.selection()
        if not selection:
            return
            
        item = self.vectors_tree.item(selection[0])
        values = item['values']
        
        # Show vector details
        details = f"Vector ID: {values[0]}\n"
        details += f"Source: {values[1]}\n"
        details += f"Chunk Index: {values[2]}\n"
        details += f"Content Preview:\n{values[3]}\n"
        
        self.vector_details.delete("1.0", "end")
        self.vector_details.insert("1.0", details)
        
    def _update_index(self, force=False):
        """Update the document index."""
        if not self.config or not self.file_processor or not self.vector_store:
            self._show_status("Project not configured. Run 'sage setup' first.")
            return
            
        def update_thread():
            try:
                # Update status
                action = "Force reindexing" if force else "Updating index"
                self.root.after(0, lambda: self._show_status(f"{action}..."))
                
                # Find files to process
                files_to_process = self.file_processor.find_files(self.project_path, force)
                
                if not files_to_process:
                    self.root.after(0, lambda: self._show_status("No files to process. Knowledge base is up to date."))
                    return
                
                if force:
                    self.vector_store.clear()
                    
                # Process files
                total_documents = 0
                processed_files = 0
                
                for i, file_path in enumerate(files_to_process):
                    try:
                        # Update progress
                        progress = f"Processing {file_path.name} ({i+1}/{len(files_to_process)})"
                        self.root.after(0, lambda p=progress: self._show_status(p))
                        
                        documents = self.file_processor.process_file(file_path)
                        if documents:
                            self.vector_store.add_documents(documents)
                            self.file_processor.update_metadata(self.project_path, file_path, documents)
                            total_documents += len(documents)
                            processed_files += 1
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
                        
                # Final status
                status = f"✅ Processed {processed_files} files, created {total_documents} document chunks"
                self.root.after(0, lambda: self._show_status(status))
                        
                # Refresh UI
                self.root.after(0, self._load_data)
                
            except Exception as e:
                error_msg = f"❌ Update error: {str(e)}"
                print(error_msg)
                self.root.after(0, lambda: self._show_status(error_msg))
                
        threading.Thread(target=update_thread, daemon=True).start()
        
    def _show_status(self, message):
        """Show status message in the overview tab."""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
        else:
            print(f"Status: {message}")
        
    # Chat functionality methods
    def _get_current_model_status(self):
        """Get current model status text."""
        if not self.model_manager:
            return "Model manager not available"
        
        current_provider, current_model = self.model_manager.get_current_model_info()
        embedding_info = self.model_manager.get_embedding_info(current_provider)
        return f"Using {current_provider.title()} {current_model} | {embedding_info}"
    
    def _on_chat_provider_change(self, provider_display):
        """Handle provider change in chat."""
        if not self.model_manager:
            return
        
        # Convert display name back to actual provider name
        provider = self.chat_provider_name_map.get(provider_display, provider_display)
        
        # Check if this provider is configured
        configured_providers = self.model_manager.get_configured_providers()
        
        if provider not in configured_providers:
            # Show warning but still allow selection to see models
            messagebox.showwarning(
                "API Key Required", 
                f"{provider.title()} is not configured with an API key.\n\n"
                f"To use {provider.title()} models:\n"
                f"1. Run 'sage setup' to add API keys\n"
                f"2. Or add {provider.upper()}_API_KEY environment variable"
            )
        
        # Update available models for this provider
        available_models = self.model_manager.get_available_models()[provider]
        self.chat_model_menu.configure(values=available_models)
        self.chat_model_var.set(available_models[0])
        
        # Only switch model if provider is configured
        if provider in configured_providers:
            self.model_manager.switch_model(provider, available_models[0])
            self._update_model_status()
        else:
            # Update status to show unavailable
            self.model_status_label.configure(
                text=f"⚠️ {provider.title()} {available_models[0]} - API Key Required"
            )
    
    def _on_chat_model_change(self, model):
        """Handle model change in chat."""
        if not self.model_manager:
            return
        
        # Get the actual provider name from the display name
        provider_display = self.chat_provider_var.get()
        provider = self.chat_provider_name_map.get(provider_display, provider_display)
        
        # Check if provider is configured
        configured_providers = self.model_manager.get_configured_providers()
        
        if provider in configured_providers:
            self.model_manager.switch_model(provider, model)
            self._update_model_status()
        else:
            # Update status to show unavailable
            self.model_status_label.configure(
                text=f"⚠️ {provider.title()} {model} - API Key Required"
            )
    
    def _update_model_status(self):
        """Update the model status label."""
        if hasattr(self, 'model_status_label'):
            self.model_status_label.configure(text=self._get_current_model_status())
    
    def _show_model_recommendations(self):
        """Show model recommendations window."""
        if not self.model_manager:
            return
            
        rec_window = ctk.CTkToplevel(self.root)
        rec_window.title("Model Recommendations")
        rec_window.geometry("800x600")
        rec_window.transient(self.root)
        rec_window.grab_set()
        
        # Title
        title = ctk.CTkLabel(
            rec_window,
            text="🤖 Model Recommendations",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        
        # Scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(rec_window)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Get recommendations
        recommendations = self.model_manager.get_detailed_recommendations()
        
        for use_case, details in recommendations.items():
            # Use case frame
            case_frame = ctk.CTkFrame(scrollable_frame)
            case_frame.pack(fill="x", pady=(0, 15))
            
            # Title and status
            title_frame = ctk.CTkFrame(case_frame, fg_color="transparent")
            title_frame.pack(fill="x", padx=15, pady=10)
            
            status_color = "green" if details["available"] else "red"
            status_text = "✅ Available" if details["available"] else "❌ Not Configured"
            
            case_title = ctk.CTkLabel(
                title_frame,
                text=f"🎯 {use_case.title()}: {details['provider'].title()} {details['model']}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            case_title.pack(side="left")
            
            status_label = ctk.CTkLabel(
                title_frame,
                text=status_text,
                font=ctk.CTkFont(size=12),
                text_color=status_color
            )
            status_label.pack(side="right")
            
            # Description
            desc_text = f"{details['description']}\n{details['embedding_info']}"
            desc_label = ctk.CTkLabel(
                case_frame,
                text=desc_text,
                font=ctk.CTkFont(size=11),
                text_color="gray",
                wraplength=700,
                justify="left"
            )
            desc_label.pack(padx=15, pady=(0, 10), fill="x")
            
            # Switch button if available
            if details["available"]:
                switch_button = ctk.CTkButton(
                    case_frame,
                    text=f"Switch to {details['provider'].title()} {details['model']}",
                    command=lambda p=details['provider'], m=details['model']: self._switch_to_model(p, m, rec_window),
                    width=200,
                    height=25
                )
                switch_button.pack(padx=15, pady=(0, 10))
        
        # Close button
        close_button = ctk.CTkButton(
            rec_window,
            text="Close",
            command=rec_window.destroy,
            width=100
        )
        close_button.pack(pady=15)
    
    def _switch_to_model(self, provider, model, window):
        """Switch to a specific model and close window."""
        if self.model_manager.switch_model(provider, model):
            self.chat_provider_var.set(provider)
            self.chat_model_var.set(model)
            self._update_model_status()
            window.destroy()
            
            # Add system message to chat
            self._add_chat_message("💬 System", 
                f"Switched to {provider.title()} {model}", 
                is_bot=True, is_system=True)
    
    def _add_chat_message(self, sender, message, is_bot=False, is_system=False):
        """Add a message to the chat history."""
        # Create message frame
        message_frame = ctk.CTkFrame(self.chat_history)
        message_frame.pack(fill="x", padx=10, pady=5)
        
        # Sender label
        sender_color = "green" if is_bot else "blue"
        if is_system:
            sender_color = "orange"
            
        sender_label = ctk.CTkLabel(
            message_frame,
            text=sender,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=sender_color
        )
        sender_label.pack(anchor="w", padx=10, pady=(5, 0))
        
        # Message content
        message_label = ctk.CTkLabel(
            message_frame,
            text=message,
            font=ctk.CTkFont(size=11),
            wraplength=700,
            justify="left",
            anchor="w"
        )
        message_label.pack(anchor="w", padx=10, pady=(0, 10), fill="x")
        
        # Scroll to bottom
        self.chat_history._parent_canvas.yview_moveto(1.0)
    
    def _send_chat_message(self, event=None):
        """Send a chat message."""
        if not self.config or not self.model_manager or not self.vector_store:
            messagebox.showerror("Error", "Project not properly configured.")
            return
        
        # Check if current provider is configured
        current_provider, current_model = self.model_manager.get_current_model_info()
        configured_providers = self.model_manager.get_configured_providers()
        
        if current_provider not in configured_providers:
            messagebox.showerror(
                "API Key Required",
                f"Cannot send message: {current_provider.title()} is not configured.\n\n"
                f"Please:\n"
                f"1. Run 'sage setup' to add API keys, or\n"
                f"2. Switch to a configured provider (✅ marked)"
            )
            return
        
        message = self.chat_entry.get().strip()
        if not message:
            return
            
        # Clear input
        self.chat_entry.delete(0, "end")
        
        # Add user message to chat
        self._add_chat_message("🧑 You", message)
        
        # Disable send button
        self.chat_send_button.configure(state="disabled", text="Thinking...")
        
        # Process message in thread
        def chat_thread():
            try:
                # Search for relevant documents
                documents = self.vector_store.search(message, k=5)
                
                if not documents:
                    self.root.after(0, lambda: self._add_chat_message("🤖 Sage", 
                        "❌ No relevant documents found for your question.", is_bot=True))
                    self.root.after(0, lambda: self.chat_send_button.configure(state="normal", text="Send"))
                    return
                
                # Get LLM client for current model
                llm_client = self.model_manager.get_llm_client()
                
                # Get answer
                result = llm_client.answer_question(message, documents)
                
                if result.get('error'):
                    error_msg = f"❌ Error: {result['answer']}\n\nPlease check your API key and internet connection."
                    self.root.after(0, lambda: self._add_chat_message("🤖 Sage", error_msg, is_bot=True))
                else:
                    # Add response to chat
                    answer_with_sources = result['answer']
                    if result['sources']:
                        sources = [Path(s).relative_to(self.project_path).name for s in result['sources']]
                        answer_with_sources += f"\n\n📚 Sources: {', '.join(sources)}"
                    
                    self.root.after(0, lambda: self._add_chat_message("🤖 Sage", answer_with_sources, is_bot=True))
                    
                    # Add to conversation history
                    self.conversation_history.append({
                        'question': message,
                        'answer': result['answer'],
                        'sources': result['sources'],
                        'model': f"{self.model_manager.get_current_model_info()[0]}:{self.model_manager.get_current_model_info()[1]}",
                        'timestamp': datetime.now().isoformat()
                    })
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}\n\nPlease check your API key configuration and internet connection."
                self.root.after(0, lambda: self._add_chat_message("🤖 Sage", error_msg, is_bot=True))
            
            finally:
                self.root.after(0, lambda: self.chat_send_button.configure(state="normal", text="Send"))
        
        threading.Thread(target=chat_thread, daemon=True).start()
    
    def _clear_chat_history(self):
        """Clear the chat history."""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            # Clear UI
            for widget in self.chat_history.winfo_children():
                widget.destroy()
                
            # Clear history
            self.conversation_history = []
            
            # Add welcome message back
            current_provider, current_model = self.model_manager.get_current_model_info()
            self._add_chat_message("🤖 Sage", 
                f"Chat cleared. Ready to help!\n\n🤖 Current model: {current_provider.title()} {current_model}", 
                is_bot=True)
    
    def _save_chat_history(self):
        """Save chat history to file."""
        if not self.conversation_history:
            messagebox.showinfo("Save Chat", "No conversation history to save.")
            return
            
        try:
            # Create chat history file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chat_file = self.project_path / f"sage_chat_{timestamp}.json"
            
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'project': str(self.project_path),
                    'timestamp': datetime.now().isoformat(),
                    'conversation_count': len(self.conversation_history),
                    'conversations': self.conversation_history
                }, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Chat Saved", f"Chat history saved to:\n{chat_file.name}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save chat history:\n{str(e)}")
    
    def _manage_api_keys(self):
        """Show API key management dialog."""
        api_window = ctk.CTkToplevel(self.root)
        api_window.title("Manage API Keys")
        api_window.geometry("600x500")
        api_window.transient(self.root)
        api_window.grab_set()
        
        # Title
        title = ctk.CTkLabel(
            api_window,
            text="🔑 API Key Management",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)
        
        # Info
        info_label = ctk.CTkLabel(
            api_window,
            text="Add API keys to enable additional providers. Keys are stored securely in your project configuration.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=550
        )
        info_label.pack(pady=10)
        
        # Scrollable frame for API keys
        scrollable_frame = ctk.CTkScrollableFrame(api_window)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # API key entries
        self.api_entries = {}
        providers_info = {
            "google": ("Google Gemini", "Get from: https://makersuite.google.com/app/apikey"),
            "anthropic": ("Anthropic Claude", "Get from: https://console.anthropic.com/"),
            "openai": ("OpenAI GPT", "Get from: https://platform.openai.com/api-keys"),
            "ollama": ("Ollama (Local)", "No API key needed - install Ollama locally")
        }
        
        configured_providers = self.model_manager.get_configured_providers()
        
        for provider, (display_name, info_text) in providers_info.items():
            # Provider frame
            provider_frame = ctk.CTkFrame(scrollable_frame)
            provider_frame.pack(fill="x", pady=10)
            
            # Status indicator
            status = "✅ Configured" if provider in configured_providers else "❌ Not Configured"
            status_color = "green" if provider in configured_providers else "red"
            
            # Header
            header_frame = ctk.CTkFrame(provider_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=10)
            
            provider_title = ctk.CTkLabel(
                header_frame,
                text=display_name,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            provider_title.pack(side="left")
            
            status_label = ctk.CTkLabel(
                header_frame,
                text=status,
                font=ctk.CTkFont(size=12),
                text_color=status_color
            )
            status_label.pack(side="right")
            
            # Info text
            info_provider_label = ctk.CTkLabel(
                provider_frame,
                text=info_text,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            info_provider_label.pack(padx=15, pady=(0, 5))
            
            if provider != "ollama":  # Ollama doesn't need API key
                # API key entry
                current_key = ""
                if provider in configured_providers:
                    current_key = "••••••••••••••••" # Show masked for existing keys
                
                api_entry = ctk.CTkEntry(
                    provider_frame,
                    placeholder_text=f"Enter {display_name} API key" if not current_key else "API key configured",
                    show="*" if not current_key else None,
                    width=500
                )
                if current_key:
                    api_entry.insert(0, current_key)
                api_entry.pack(padx=15, pady=(0, 15), fill="x")
                self.api_entries[provider] = api_entry
        
        # Buttons
        button_frame = ctk.CTkFrame(api_window, fg_color="transparent")
        button_frame.pack(pady=20)
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Save API Keys",
            command=lambda: self._save_api_keys(api_window),
            width=120
        )
        save_button.pack(side="left", padx=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=api_window.destroy,
            width=120,
            fg_color="gray"
        )
        cancel_button.pack(side="left", padx=5)
    
    def _save_api_keys(self, window):
        """Save API keys to configuration."""
        try:
            # Get new API keys
            new_keys = {}
            for provider, entry in self.api_entries.items():
                key = entry.get().strip()
                if key and key != "••••••••••••••••":  # Not the masked existing key
                    new_keys[provider] = key
            
            if not new_keys:
                messagebox.showinfo("No Changes", "No new API keys to save.")
                window.destroy()
                return
            
            # Update config with new API keys
            from pydantic import SecretStr
            
            # Create a copy of config to avoid modifying original
            updated_config = self.config.model_copy(deep=True)
            
            for provider, key in new_keys.items():
                if provider == "google":
                    updated_config.google_api_key = SecretStr(key)
                elif provider == "anthropic":
                    updated_config.anthropic_api_key = SecretStr(key)
                elif provider == "openai":
                    updated_config.openai_api_key = SecretStr(key)
            
            # Save updated config
            self.config_manager.save(updated_config)
            
            # Update the config reference
            self.config = updated_config
            
            # Refresh model manager with new config
            self.model_manager = ModelManager(self.config)
            
            # Update provider dropdowns
            self._refresh_provider_dropdown()
            
            # Get the count of newly configured providers
            configured_providers = self.model_manager.get_configured_providers()
            
            messagebox.showinfo(
                "Success", 
                f"API keys saved successfully!\n\n"
                f"Added: {', '.join(new_keys.keys())}\n"
                f"Total configured providers: {len(configured_providers)}"
            )
            window.destroy()
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"API Key Save Error: {error_details}")  # For debugging
            messagebox.showerror("Error", f"Failed to save API keys:\n{str(e)}\n\nCheck console for details.")
    
    def _refresh_provider_dropdown(self):
        """Refresh the provider dropdown with updated availability."""
        if not hasattr(self, 'chat_provider_menu'):
            return
        
        # Get updated provider info
        all_providers = list(self.model_manager.get_available_models().keys())
        configured_providers = self.model_manager.get_configured_providers()
        
        # Update provider display names
        provider_display_names = []
        provider_name_map = {}
        
        for provider in all_providers:
            if provider in configured_providers:
                display_name = f"✅ {provider.title()}"
            else:
                display_name = f"❌ {provider.title()} (No API Key)"
            provider_display_names.append(display_name)
            provider_name_map[display_name] = provider
        
        # Update the dropdown
        self.chat_provider_name_map = provider_name_map
        self.chat_provider_menu.configure(values=provider_display_names)
        
        # Update status
        self._update_model_status()
        
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for the GUI application."""
    import sys
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path.cwd()
        
    app = SageGUI(project_path)
    app.run()


if __name__ == "__main__":
    main()