# Dual Model Setup - Separate Index & Chat Models

This document describes the enhanced setup functionality that allows you to choose **different models for indexing and chat** during initial project configuration.

## 🎯 Why Separate Models?

Previously, Sage used the same model for both document indexing (creating embeddings) and chat responses. Now you can optimize each use case separately:

### **Indexing/Embeddings** 📚
- **Purpose**: Process and understand your documents for search
- **Key Factors**: Multilingual support, embedding quality, cost per document
- **Recommendation**: Google models (best multilingual embeddings, especially for Vietnamese/Chinese)

### **Chat/Responses** 💬  
- **Purpose**: Generate responses during conversations
- **Key Factors**: Response quality, reasoning ability, speed, conversational skills
- **Recommendation**: Anthropic Claude (best reasoning) or OpenAI GPT (latest features)

## 🚀 Enhanced Setup Interface

The new setup GUI features **3 dedicated tabs**:

### 📚 **Indexing & Embeddings Tab**
- Choose the provider and model for document processing
- Optimized for search quality and multilingual support
- **Fixed after setup** - affects all future document indexing

### 💬 **Chat & Responses Tab**
- Choose the provider and model for chat conversations
- **Can be changed anytime** in the main GUI
- Optimized for response quality and reasoning

### 🔑 **API Keys Tab**
- Centralized API key management for all providers
- Only enter keys for providers you selected
- Secure storage in project configuration

## 🎯 Recommended Combinations

### 1. **Multilingual Specialist** 🌍
```
📚 Index: Google Gemini 1.5 Pro (best multilingual embeddings)
💬 Chat: Anthropic Claude 3.5 Sonnet (best reasoning)
🎯 Best for: Vietnamese, Chinese, or other non-English documents
```

### 2. **Speed Demon** ⚡
```
📚 Index: Google Gemini 1.5 Flash (fast, efficient)
💬 Chat: Google Gemini 2.0 Flash Exp (latest, fastest)
🎯 Best for: Quick prototyping, real-time applications
```

### 3. **Privacy First** 🔒
```
📚 Index: Ollama Llama 3.1 8B (local embeddings)
💬 Chat: Ollama Llama 3.1 70B (local chat)
🎯 Best for: Complete privacy, no cloud API calls
```

### 4. **Reasoning Master** 🧠
```
📚 Index: OpenAI text-embedding-3-large (good embeddings)
💬 Chat: OpenAI o1-preview (best reasoning)
🎯 Best for: Complex analysis, math, logic problems
```

### 5. **Single Provider** 🏢
```
📚 Index: OpenAI GPT-4o (good embeddings)
💬 Chat: OpenAI GPT-4o (same model)
🎯 Best for: Simplicity, single API key management
```

## 🛠️ How to Use

### 1. **Run Enhanced Setup**
```bash
sage setup
```

### 2. **Configure Each Tab**

#### **📚 Indexing & Embeddings**
1. Select your preferred provider for document processing
2. Choose the model (consider multilingual support)
3. This choice affects search quality and is **permanent**

#### **💬 Chat & Responses**  
1. Select your preferred provider for conversations
2. Choose the model (consider response quality)
3. You can **change this anytime** in the main GUI

#### **🔑 API Keys**
1. Enter API keys for the providers you selected
2. You only need keys for providers you're actually using
3. Ollama doesn't require an API key (local model)

### 3. **Complete Setup**
- The system validates you have API keys for selected providers
- Configuration is saved with separate index and chat settings
- Ready to use with optimized models for each purpose!

## 🔧 Technical Implementation

### **Configuration Structure**
```python
config = SageConfig(
    # New separate configuration
    index_provider="google",           # For embeddings
    index_model="gemini-1.5-pro",     # High quality indexing
    chat_provider="anthropic",         # For responses  
    chat_model="claude-3-sonnet",     # Best reasoning
    
    # API keys for each provider
    google_api_key=SecretStr("..."),
    anthropic_api_key=SecretStr("..."),
    
    # Legacy fields (backwards compatibility)
    llm_provider="google",             # Fallback
    llm_model="gemini-1.5-pro",       # Fallback
)
```

### **Smart API Key Resolution**
```python
# Get the right API key for each purpose
index_key = config.get_index_api_key()    # Uses Google key
chat_key = config.get_chat_api_key()      # Uses Anthropic key
```

### **Backwards Compatibility**
- Existing configurations continue to work
- Old configs use the same model for both index and chat
- New method calls handle both old and new config formats seamlessly

## 💡 Best Practices

### **For Multilingual Documents**
- **Always use Google** for indexing (best embeddings for Vietnamese, Chinese, etc.)
- Chat model can be any provider based on your quality preferences

### **For Performance**
- Use faster models (Flash, Haiku) for indexing if speed is critical
- Use high-quality models (Pro, Opus) for chat if accuracy matters

### **For Cost Optimization**  
- Use efficient models (Flash, Mini) for high-volume indexing
- Use premium models selectively for important chat conversations

### **For Privacy**
- Use Ollama for both if you need complete data privacy
- Consider local indexing + cloud chat for balanced privacy/quality

## 📊 Model Comparison

| Provider | Best Index Models | Best Chat Models | Strengths |
|----------|-------------------|------------------|-----------|
| **Google** | gemini-1.5-pro | gemini-2.0-flash-exp | Best multilingual, fast |
| **Anthropic** | *(use Google)* | claude-3.5-sonnet | Best reasoning, writing |
| **OpenAI** | text-embedding-3-large | o1-preview | Latest features, reasoning |
| **Ollama** | llama3.1:8b | llama3.1:70b | Complete privacy, no cost |

## 🔄 Migration from Single Model

If you have an existing Sage project with single model configuration:

1. **Your current setup continues to work** - no changes needed
2. **To upgrade to dual models**: Run `sage setup` again
3. **Choose different models** for index vs chat
4. **Existing documents don't need re-indexing** unless you change the index model

## 🎉 Benefits

✅ **Optimized Performance**: Best model for each specific task
✅ **Cost Efficiency**: Use cheaper models where appropriate  
✅ **Multilingual Excellence**: Google embeddings + any chat model
✅ **Flexibility**: Change chat models without affecting search
✅ **Provider Diversity**: Mix and match different AI providers
✅ **Backwards Compatible**: Existing projects continue to work
✅ **Future-Proof**: Easy to adopt new models as they're released

---

The enhanced setup empowers you to create the perfect AI configuration for your specific needs, balancing quality, speed, cost, and privacy across indexing and chat functionality! 🚀