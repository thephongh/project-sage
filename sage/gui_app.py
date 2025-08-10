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
        if self.config:
            self.file_processor = FileProcessor(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                ocr_language=self.config.document_language
            )
            self.vector_store = VectorStore(self.config)
            self.vector_store.initialize()
            self.llm_client = LLMClient(self.config)
            
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
        self.query_tab = self.notebook.add("Query")
        self.config_tab = self.notebook.add("Config")
        
        self._create_overview_tab()
        self._create_files_tab()
        self._create_vectors_tab()
        self._create_query_tab()
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
        stats = [
            ("Project Path", str(self.project_path)),
            ("Configuration", "Loaded" if self.config else "Not configured"),
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
        
    def _create_query_tab(self):
        """Create the query tab for asking questions."""
        # Query input frame
        input_frame = ctk.CTkFrame(self.query_tab)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            input_frame, 
            text="Ask a Question",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        query_container = ctk.CTkFrame(input_frame)
        query_container.pack(fill="x", padx=10, pady=5)
        
        self.query_entry = ctk.CTkEntry(
            query_container, 
            placeholder_text="Enter your question about the project documents..."
        )
        self.query_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.query_entry.bind("<Return>", self._ask_question)
        
        self.ask_button = ctk.CTkButton(
            query_container,
            text="Ask",
            command=self._ask_question,
            width=100
        )
        self.ask_button.pack(side="right", padx=5)
        
        # Response frame
        response_frame = ctk.CTkFrame(self.query_tab)
        response_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            response_frame, 
            text="Response",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.response_text = ctk.CTkTextbox(response_frame)
        self.response_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Sources frame
        sources_frame = ctk.CTkFrame(self.query_tab)
        sources_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            sources_frame, 
            text="Sources",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.sources_text = ctk.CTkTextbox(sources_frame, height=100)
        self.sources_text.pack(fill="x", padx=10, pady=5)
        
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
        
        config_data = {
            "Project Path": str(self.config.project_path),
            "LLM Provider": self.config.llm_provider,
            "LLM Model": self.config.llm_model,
            "Document Language": self.config.document_language,
            "Embedding Model": self.config.embedding_model,
            "Chunk Size": str(self.config.chunk_size),
            "Chunk Overlap": str(self.config.chunk_overlap)
        }
        
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
        
    def _ask_question(self, event=None):
        """Ask a question using the LLM."""
        if not self.config or not self.llm_client or not self.vector_store:
            self.response_text.delete("1.0", "end")
            self.response_text.insert("1.0", "Project not properly configured.")
            return
            
        query = self.query_entry.get().strip()
        if not query:
            return
            
        def query_thread():
            try:
                # Disable button and show progress
                def start_query():
                    self.ask_button.configure(state="disabled", text="Thinking...")
                    self.response_text.delete("1.0", "end")
                    self.response_text.insert("1.0", "🔍 Searching knowledge base...")
                    
                self.root.after(0, start_query)
                
                # Search for relevant documents
                documents = self.vector_store.search(query, k=5)
                
                if not documents:
                    def no_docs():
                        self.response_text.delete("1.0", "end")
                        self.response_text.insert("1.0", "❌ No relevant documents found for your query.")
                        self.ask_button.configure(state="normal", text="Ask")
                    self.root.after(0, no_docs)
                    return
                    
                def generating():
                    self.response_text.delete("1.0", "end")
                    self.response_text.insert("1.0", "🤖 Generating answer...")
                    
                self.root.after(0, generating)
                
                # Get answer from LLM
                result = self.llm_client.answer_question(query, documents)
                
                # Update UI with results
                def update_response():
                    self.response_text.delete("1.0", "end")
                    self.response_text.insert("1.0", result['answer'])
                    
                    sources_text = "📚 Sources:\n"
                    for source in result['sources']:
                        try:
                            rel_path = Path(source).relative_to(self.project_path)
                            sources_text += f"• {rel_path}\n"
                        except:
                            sources_text += f"• {source}\n"
                            
                    self.sources_text.delete("1.0", "end")
                    self.sources_text.insert("1.0", sources_text)
                    
                    self.ask_button.configure(state="normal", text="Ask")
                    
                self.root.after(0, update_response)
                
            except Exception as e:
                def show_error():
                    error_msg = f"❌ Error: {str(e)}\n\nPlease check your:\n• API key configuration\n• Internet connection\n• LLM provider settings"
                    self.response_text.delete("1.0", "end")
                    self.response_text.insert("1.0", error_msg)
                    self.ask_button.configure(state="normal", text="Ask")
                    
                self.root.after(0, show_error)
                
        threading.Thread(target=query_thread, daemon=True).start()
        
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