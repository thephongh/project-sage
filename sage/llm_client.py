"""LLM client for Project Sage."""

from typing import List, Optional, Dict, Any
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

try:
    from langchain_ollama import ChatOllama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


class LLMClient:
    """Manages LLM interactions for question answering."""
    
    SYSTEM_PROMPT = """You are an intelligent project assistant called Sage. Your role is to help project managers understand and analyze their project documents.

You will be provided with context from project documents, which may be in various languages (particularly Vietnamese). Your task is to:
1. Analyze the provided context carefully
2. Answer the user's question based ONLY on the information in the context
3. Provide clear, concise answers in English
4. If the context is in a different language, translate relevant portions as needed
5. Always cite the sources of your information

If the provided context doesn't contain enough information to answer the question, say so clearly.

Context from documents:
{context}

Question: {question}

Please provide a comprehensive answer in English:"""
    
    def __init__(self, config):
        self.config = config
        self.llm = self._get_llm()
        self.chain = self._create_chain()
        
    def _get_llm(self):
        """Get the appropriate LLM based on provider."""
        api_key = self.config.api_key.get_secret_value()
        
        if self.config.llm_provider == "google":
            return ChatGoogleGenerativeAI(
                model=self.config.llm_model,
                google_api_key=api_key,
                temperature=0.3,
                max_output_tokens=2048
            )
        elif self.config.llm_provider == "anthropic":
            return ChatAnthropic(
                model=self.config.llm_model,
                anthropic_api_key=api_key,
                temperature=0.3,
                max_tokens=2048
            )
        elif self.config.llm_provider == "openai":
            return ChatOpenAI(
                model=self.config.llm_model,
                openai_api_key=api_key,
                temperature=0.3,
                max_tokens=2048
            )
        elif self.config.llm_provider == "ollama":
            if not HAS_OLLAMA:
                raise ValueError("Ollama support not installed. Run: pip install langchain-ollama")
                
            base_url = self.config.ollama_url or "http://localhost:11434"
            
            # Handle API key for secured Ollama instances (optional)
            ollama_kwargs = {
                "model": self.config.llm_model,
                "base_url": base_url,
                "temperature": 0.3,
            }
            
            # Only add API key if provided and not the default
            if api_key and api_key != "not-required":
                ollama_kwargs["api_key"] = api_key
                
            return ChatOllama(**ollama_kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.config.llm_provider}")
            
    def _create_chain(self):
        """Create the LLM chain for question answering."""
        prompt = ChatPromptTemplate.from_template(self.SYSTEM_PROMPT)
        return LLMChain(llm=self.llm, prompt=prompt)
        
    def answer_question(self, question: str, documents: List[Document]) -> Dict[str, Any]:
        """Answer a question based on retrieved documents."""
        # Format context from documents
        context_parts = []
        sources = set()
        
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Unknown')
            chunk_idx = doc.metadata.get('chunk_index', 0)
            total_chunks = doc.metadata.get('total_chunks', 1)
            
            context_parts.append(f"[Document {i} - {source} (chunk {chunk_idx+1}/{total_chunks})]")
            context_parts.append(doc.page_content)
            context_parts.append("")
            
            sources.add(source)
            
        context = "\n".join(context_parts)
        
        # Get answer from LLM
        try:
            response = self.chain.invoke({
                "context": context,
                "question": question
            })
            
            answer = response['text']
            
            return {
                "answer": answer,
                "sources": list(sources),
                "documents_used": len(documents)
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": list(sources),
                "documents_used": len(documents),
                "error": True
            }