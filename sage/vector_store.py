"""Vector database management for Project Sage."""

from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

try:
    from langchain_ollama import OllamaEmbeddings
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False


class VectorStore:
    """Manages the vector database for document storage and retrieval."""
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.project_path / ".sage/db"
        self.embeddings = self._get_embeddings()
        self.vectorstore = None
        
    def _get_embeddings(self):
        """Get the appropriate embeddings model based on provider."""
        api_key = self.config.api_key.get_secret_value()
        
        if self.config.llm_provider == "google":
            return GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key
            )
        elif self.config.llm_provider == "anthropic":
            # Anthropic doesn't have native embeddings, use OpenAI as fallback
            # User would need to provide OpenAI API key for embeddings
            return OpenAIEmbeddings(
                model="text-embedding-3-small"
            )
        elif self.config.llm_provider == "openai":
            return OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key
            )
        elif self.config.llm_provider == "ollama":
            # For Ollama, try to use Ollama embeddings first, fall back to local HuggingFace
            base_url = self.config.ollama_url or "http://localhost:11434"
            
            if HAS_OLLAMA:
                try:
                    # Try to use Ollama's embedding model (e.g., nomic-embed-text)
                    return OllamaEmbeddings(
                        model="nomic-embed-text",  # Popular embedding model on Ollama
                        base_url=base_url
                    )
                except Exception:
                    # Fall back to local HuggingFace embeddings
                    pass
                    
            # Fallback to local HuggingFace embeddings for Ollama
            if HAS_HUGGINGFACE:
                return HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'}
                )
            else:
                raise ValueError(
                    "Ollama embeddings require either:\n"
                    "1. Ollama with nomic-embed-text model installed, or\n"
                    "2. HuggingFace embeddings. Install with: pip install sentence-transformers"
                )
        else:
            raise ValueError(f"Unsupported provider: {self.config.llm_provider}")
            
    def initialize(self):
        """Initialize or load the vector store."""
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB with persistent storage
        self.vectorstore = Chroma(
            collection_name="sage_documents",
            embedding_function=self.embeddings,
            persist_directory=str(self.db_path)
        )
        
    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store."""
        if not self.vectorstore:
            self.initialize()
            
        if documents:
            self.vectorstore.add_documents(documents)
            
    def clear(self):
        """Clear all documents from the vector store."""
        if self.vectorstore:
            # Get all document IDs and delete them
            collection = self.vectorstore._collection
            all_ids = collection.get()['ids']
            if all_ids:
                collection.delete(ids=all_ids)
                
    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant documents."""
        if not self.vectorstore:
            self.initialize()
            
        return self.vectorstore.similarity_search(query, k=k)
        
    def search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Search for relevant documents with relevance scores."""
        if not self.vectorstore:
            self.initialize()
            
        return self.vectorstore.similarity_search_with_score(query, k=k)
        
    def get_document_count(self) -> int:
        """Get the total number of documents in the store."""
        if not self.vectorstore:
            self.initialize()
            
        collection = self.vectorstore._collection
        return collection.count()