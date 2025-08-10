"""File processing and document loading for Project Sage."""

import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.xlsx import partition_xlsx
from unstructured.partition.text import partition_text
from unstructured.partition.md import partition_md
import pytesseract
from PIL import Image

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class FileProcessor:
    """Processes various file types for indexing."""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.pptx', '.xlsx', '.txt', '.md'
    }
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300, ocr_language: str = "eng"):
        # Enhanced chunk size for better context preservation
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.ocr_language = ocr_language
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            # Better separators for Vietnamese and structured documents
            separators=["\n\n", "\n", ". ", "。", "! ", "? ", " ", ""]
        )
        self.metadata_file = ".sage/file_metadata.json"
    
    def _extract_folder_context(self, file_path: Path, project_path: Path) -> Dict[str, str]:
        """Extract hierarchical context from folder structure."""
        try:
            # Get relative path from project root
            rel_path = file_path.relative_to(project_path)
            path_parts = list(rel_path.parts[:-1])  # Exclude filename
            
            # Create hierarchical context
            context = {
                "project_category": "",
                "main_phase": "",
                "sub_category": "",
                "specific_area": "",
                "folder_hierarchy": " > ".join(path_parts) if path_parts else "root"
            }
            
            if len(path_parts) >= 1:
                # Main project phase (01.Origination&Dev, 02.Execution, 03.Operation)
                context["main_phase"] = path_parts[0]
                
            if len(path_parts) >= 2:
                # Project category (Project_Management, ACES, Studies_Design, etc.)
                context["project_category"] = path_parts[1]
                
            if len(path_parts) >= 3:
                # Sub category (Meetings, Budget_DevEx, etc.)
                context["sub_category"] = path_parts[2]
                
            if len(path_parts) >= 4:
                # Specific area (detailed breakdown)
                context["specific_area"] = path_parts[3]
            
            # Create descriptive context for embeddings
            if context["main_phase"]:
                phase_desc = {
                    "01.Origination&Dev": "Project Development and Origination Phase",
                    "02.Execution": "Project Construction and Execution Phase", 
                    "03.Operation": "Project Operation and Maintenance Phase"
                }.get(context["main_phase"], context["main_phase"])
                context["phase_description"] = phase_desc
            
            return context
            
        except Exception:
            return {
                "project_category": "unknown",
                "main_phase": "unknown", 
                "sub_category": "unknown",
                "specific_area": "unknown",
                "folder_hierarchy": "unknown",
                "phase_description": "Unknown project phase"
            }
        
    def load_metadata(self, project_path: Path) -> Dict[str, Dict]:
        """Load file metadata from cache."""
        metadata_path = project_path / self.metadata_file
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return {}
        
    def save_metadata(self, project_path: Path, metadata: Dict[str, Dict]):
        """Save file metadata to cache."""
        metadata_path = project_path / self.metadata_file
        os.makedirs(metadata_path.parent, exist_ok=True)
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def find_files(self, project_path: Path, force: bool = False) -> List[Path]:
        """Find all supported files in the project directory."""
        files_to_process = []
        metadata = self.load_metadata(project_path) if not force else {}
        
        for ext in self.SUPPORTED_EXTENSIONS:
            for file_path in project_path.rglob(f"*{ext}"):
                # Skip files in .sage directory
                if ".sage" in str(file_path):
                    continue
                    
                file_str = str(file_path)
                file_hash = self.get_file_hash(file_path)
                
                # Check if file needs processing
                if force or file_str not in metadata or metadata[file_str].get('hash') != file_hash:
                    files_to_process.append(file_path)
                    
        return files_to_process
        
    def process_file(self, file_path: Path, project_path: Path = None) -> List[Document]:
        """Process a single file and return documents with enhanced context."""
        ext = file_path.suffix.lower()
        
        try:
            if ext == '.pdf':
                elements = self._process_pdf(file_path)
            elif ext == '.docx':
                elements = partition_docx(filename=str(file_path))
            elif ext == '.pptx':
                elements = partition_pptx(filename=str(file_path))
            elif ext == '.xlsx':
                elements = partition_xlsx(filename=str(file_path))
            elif ext == '.txt':
                elements = partition_text(filename=str(file_path))
            elif ext == '.md':
                elements = partition_md(filename=str(file_path))
            else:
                elements = partition(filename=str(file_path))
                
            # Convert elements to text
            original_text = "\n\n".join([str(el) for el in elements])
            
            # Extract folder context if project_path provided
            folder_context = {}
            context_prefix = ""
            if project_path:
                folder_context = self._extract_folder_context(file_path, project_path)
                # Create context prefix to help with embeddings
                context_prefix = f"""
Document Context:
- Project Phase: {folder_context.get('phase_description', 'Unknown')}
- Category: {folder_context.get('project_category', 'Unknown')}
- Location: {folder_context.get('folder_hierarchy', 'Unknown')}
- File: {file_path.name}

Content:
"""
            
            # Enhance text with context for better embeddings
            enhanced_text = context_prefix + original_text
            
            # Create comprehensive metadata
            metadata = {
                "source": str(file_path),
                "file_type": ext,
                "processed_at": datetime.now().isoformat(),
                **folder_context  # Include all folder context
            }
            
            # Split enhanced text into chunks
            documents = self.text_splitter.create_documents(
                texts=[enhanced_text],
                metadatas=[metadata]
            )
            
            # Add chunk index and ensure context is preserved
            for i, doc in enumerate(documents):
                doc.metadata["chunk_index"] = i
                doc.metadata["total_chunks"] = len(documents)
                # Add search-friendly context
                doc.metadata["search_context"] = (
                    f"{folder_context.get('phase_description', '')} "
                    f"{folder_context.get('project_category', '')} "
                    f"{folder_context.get('folder_hierarchy', '')}"
                ).strip()
                
            return documents
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return []
            
    def _process_pdf(self, file_path: Path) -> List:
        """Process PDF with OCR support for scanned documents."""
        try:
            # Try regular text extraction first
            elements = partition_pdf(
                filename=str(file_path),
                strategy="auto",
                languages=[self.ocr_language] if self.ocr_language != "eng" else None
            )
            
            # Check if we got meaningful text
            text_content = " ".join([str(el) for el in elements])
            if len(text_content.strip()) < 100:
                # Likely a scanned document, use OCR
                elements = partition_pdf(
                    filename=str(file_path),
                    strategy="ocr_only",
                    languages=[self.ocr_language],
                    ocr_languages=self.ocr_language
                )
                
            return elements
            
        except Exception as e:
            print(f"Error with PDF processing, attempting OCR: {str(e)}")
            # Fallback to pure OCR
            try:
                elements = partition_pdf(
                    filename=str(file_path),
                    strategy="ocr_only",
                    languages=[self.ocr_language],
                    ocr_languages=self.ocr_language
                )
                return elements
            except Exception as ocr_error:
                print(f"OCR failed for {file_path}: {str(ocr_error)}")
                return []
                
    def update_metadata(self, project_path: Path, file_path: Path, documents: List[Document]):
        """Update metadata for processed file."""
        metadata = self.load_metadata(project_path)
        
        metadata[str(file_path)] = {
            "hash": self.get_file_hash(file_path),
            "processed_at": datetime.now().isoformat(),
            "chunk_count": len(documents),
            "language": self.ocr_language
        }
        
        self.save_metadata(project_path, metadata)