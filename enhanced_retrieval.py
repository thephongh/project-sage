#!/usr/bin/env python3
"""Enhanced retrieval configuration for multi-document scenarios."""

from pathlib import Path
from sage.config import SageConfig, ConfigManager
from sage.vector_store import VectorStore
from sage.llm_client import LLMClient
from typing import List, Dict, Set
from langchain.schema import Document

class EnhancedRetrieval:
    """Enhanced retrieval for better multi-document handling."""
    
    def __init__(self, config: SageConfig):
        self.config = config
        self.vector_store = VectorStore(config)
        self.vector_store.initialize()
        
    def retrieve_with_document_diversity(self, query: str, k: int = 10, max_per_doc: int = 2) -> List[Document]:
        """
        Retrieve chunks ensuring document diversity.
        
        Args:
            query: Search query
            k: Total chunks to retrieve initially
            max_per_doc: Maximum chunks from same document
        
        Returns:
            Diverse set of chunks from multiple documents
        """
        # Get more chunks initially
        all_chunks = self.vector_store.search_with_score(query, k=k)
        
        # Track chunks per document
        doc_chunks = {}
        selected_chunks = []
        
        for chunk, score in all_chunks:
            source = chunk.metadata.get('source', 'unknown')
            
            # Initialize counter for this document
            if source not in doc_chunks:
                doc_chunks[source] = 0
            
            # Add chunk if under limit for this document
            if doc_chunks[source] < max_per_doc:
                selected_chunks.append(chunk)
                doc_chunks[source] += 1
                
            # Stop if we have enough diverse chunks
            if len(selected_chunks) >= k // 2:
                break
                
        return selected_chunks
    
    def retrieve_with_context_expansion(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieve chunks and expand context from same documents.
        
        Args:
            query: Search query
            k: Number of primary chunks
            
        Returns:
            Chunks with expanded context from same documents
        """
        # Get primary chunks
        primary_chunks = self.vector_store.search(query, k=k)
        
        expanded_chunks = []
        seen_sources = set()
        
        for chunk in primary_chunks:
            source = chunk.metadata.get('source')
            chunk_idx = chunk.metadata.get('chunk_index', 0)
            
            # Add primary chunk
            expanded_chunks.append(chunk)
            
            # If first time seeing this document, try to get adjacent chunks
            if source and source not in seen_sources:
                seen_sources.add(source)
                
                # Try to get previous and next chunks
                # Note: This would require additional vector store methods
                # For now, we'll just mark that this could be enhanced
                
        return expanded_chunks
    
    def retrieve_by_document_category(self, query: str, categories: List[str], k_per_category: int = 2) -> List[Document]:
        """
        Retrieve chunks from specific project categories.
        
        Args:
            query: Search query
            categories: List of categories like ["01.Origination&Dev", "02.Execution"]
            k_per_category: Chunks per category
            
        Returns:
            Balanced chunks from requested categories
        """
        all_chunks = []
        
        for category in categories:
            # Enhance query with category context
            category_query = f"{query} {category}"
            chunks = self.vector_store.search(category_query, k=k_per_category)
            
            # Filter to ensure chunks are actually from this category
            category_chunks = [
                chunk for chunk in chunks
                if category in chunk.metadata.get('folder_hierarchy', '')
            ]
            
            all_chunks.extend(category_chunks)
            
        return all_chunks
    
    def analyze_retrieved_documents(self, chunks: List[Document]) -> Dict:
        """
        Analyze the diversity and coverage of retrieved chunks.
        
        Args:
            chunks: Retrieved document chunks
            
        Returns:
            Analysis of document coverage
        """
        analysis = {
            'total_chunks': len(chunks),
            'unique_documents': set(),
            'project_phases': set(),
            'categories': set(),
            'document_distribution': {}
        }
        
        for chunk in chunks:
            source = chunk.metadata.get('source', 'unknown')
            phase = chunk.metadata.get('main_phase', 'unknown')
            category = chunk.metadata.get('project_category', 'unknown')
            
            analysis['unique_documents'].add(source)
            analysis['project_phases'].add(phase)
            analysis['categories'].add(category)
            
            # Count chunks per document
            if source not in analysis['document_distribution']:
                analysis['document_distribution'][source] = 0
            analysis['document_distribution'][source] += 1
        
        # Convert sets to lists for better display
        analysis['unique_documents'] = list(analysis['unique_documents'])
        analysis['project_phases'] = list(analysis['project_phases'])
        analysis['categories'] = list(analysis['categories'])
        
        return analysis

def demonstrate_multi_document_retrieval():
    """Demonstrate multi-document retrieval strategies."""
    
    print("🔍 Multi-Document Retrieval Strategies")
    print("=" * 50)
    
    strategies = [
        {
            "name": "Standard Retrieval (Current)",
            "description": "Top 5 chunks by relevance",
            "pros": "Fast, simple, works well for focused queries",
            "cons": "Might over-sample from one very relevant document",
            "example": "5 chunks, possibly all from same document"
        },
        {
            "name": "Document Diversity",
            "description": "Max 2 chunks per document, ensures variety",
            "pros": "Better coverage across multiple documents",
            "cons": "Might miss highly relevant chunks from same doc",
            "example": "5 chunks from at least 3 different documents"
        },
        {
            "name": "Category-Based Retrieval",
            "description": "Retrieve from specific project phases/categories",
            "pros": "Ensures comprehensive coverage across project phases",
            "cons": "Requires knowing which categories to search",
            "example": "2 chunks from Dev, 2 from Execution, 1 from Operation"
        },
        {
            "name": "Context Expansion",
            "description": "Retrieve chunks + adjacent chunks from same docs",
            "pros": "More complete context from each document",
            "cons": "Uses more tokens, might be redundant",
            "example": "5 primary + adjacent chunks for fuller context"
        }
    ]
    
    for i, strategy in enumerate(strategies, 1):
        print(f"\n{i}. {strategy['name']}")
        print(f"   📋 {strategy['description']}")
        print(f"   ✅ Pros: {strategy['pros']}")
        print(f"   ⚠️  Cons: {strategy['cons']}")
        print(f"   📊 Example: {strategy['example']}")

def example_multi_document_queries():
    """Show example queries that benefit from multi-document retrieval."""
    
    print("\n\n📚 Example Multi-Document Queries")
    print("=" * 50)
    
    examples = [
        {
            "query": "What are all the project risks and their mitigation strategies?",
            "documents_needed": [
                "Risk matrices from Development phase",
                "Construction risk assessments",
                "Operational risk reports",
                "Insurance documents",
                "Meeting notes on risk discussions"
            ],
            "optimal_strategy": "Document Diversity"
        },
        {
            "query": "Compare planned budget vs actual costs across all phases",
            "documents_needed": [
                "Development budget plans",
                "Execution invoices and payments",
                "Operation maintenance costs",
                "Financial model projections",
                "Budget variance reports"
            ],
            "optimal_strategy": "Category-Based Retrieval"
        },
        {
            "query": "What are all permits and their current status?",
            "documents_needed": [
                "Concession permits",
                "Environmental licenses",
                "Building permits",
                "Operating licenses",
                "Permit tracking spreadsheets"
            ],
            "optimal_strategy": "Document Diversity"
        },
        {
            "query": "Summarize all contractor agreements and key terms",
            "documents_needed": [
                "EPC contracts",
                "O&M agreements",
                "Module supply contracts",
                "Consultant agreements",
                "Contract amendments"
            ],
            "optimal_strategy": "Context Expansion"
        }
    ]
    
    for example in examples:
        print(f"\n❓ Query: '{example['query']}'")
        print(f"   📄 Needs documents from:")
        for doc in example['documents_needed']:
            print(f"      • {doc}")
        print(f"   🎯 Best strategy: {example['optimal_strategy']}")

if __name__ == "__main__":
    demonstrate_multi_document_retrieval()
    example_multi_document_queries()
    
    print("\n\n💡 Recommendations for Your Use Case:")
    print("=" * 50)
    print("""
1. For comprehensive project overviews:
   → Increase k to 10-15 chunks
   → Use document diversity to ensure coverage

2. For specific technical details:
   → Keep k at 5 but use focused queries
   → Include folder context in query (e.g., "in ACES permits")

3. For cross-phase comparisons:
   → Use category-based retrieval
   → Query each phase separately then combine

4. For contract/document analysis:
   → Use context expansion for complete clauses
   → Consider retrieving all chunks from critical documents
    """)