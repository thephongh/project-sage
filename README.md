# Project Sage

An intelligent AI assistant for complex project management that creates a self-contained knowledge base from your project documents.

## Features

- **Multi-format Support**: Process PDFs (including scanned), DOCX, PPTX, XLSX, TXT, and MD files
- **OCR Capability**: Extract text from scanned documents using Tesseract OCR
- **Multilingual**: Support for documents in multiple languages (Vietnamese, Chinese, Japanese, etc.)
- **RAG-powered Q&A**: Ask questions about your project and get contextual answers
- **Enhanced GUI Interface**: 
  - File browser showing all indexed documents
  - Vector database viewer with document chunks
  - Interactive query interface
  - Real-time project statistics
  - Configuration management
- **Simple Setup**: Easy initialization with a graphical setup wizard
- **Multiple LLM Providers**: Support for Google Gemini, Anthropic Claude, and OpenAI GPT

## Installation

### Prerequisites

1. Python 3.9 or higher
2. Tesseract OCR (required for scanned documents)

#### Installing Tesseract OCR

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # For additional language support
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-vie  # For Vietnamese
sudo apt-get install tesseract-ocr-chi-sim  # For Chinese Simplified
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Project Sage

```bash
# Clone the repository
git clone https://github.com/yourusername/project-sage.git
cd project-sage

# Install the package
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Quick Start

1. **Navigate to your project directory:**
   ```bash
   cd /path/to/your/project
   ```

2. **Initialize Sage:**
   ```bash
   sage setup
   ```
   This will open a GUI window where you can:
   - Confirm your project directory
   - Enter your LLM API key
   - Select your LLM provider and model
   - Choose the primary language of your documents

3. **Index your documents:**
   ```bash
   sage update
   ```
   This scans all supported files in your project directory and creates a searchable knowledge base.

4. **Ask questions:**
   ```bash
   sage ask "What was the agreed price in the turbine contract?"
   ```

## Commands

### `sage setup`
Launch the GUI setup window to initialize Sage for your project.

### `sage gui`
Launch the enhanced GUI application with file browser, vector viewer, and interactive query interface.

### `sage update [--force]`
Scan and index project documents. Use `--force` to re-index all files.

### `sage ask "<question>"`
Ask a single question about your project documents.

### `sage chat`
Start an interactive chat session with your documents - like Claude Code! Features:
- Continuous conversation with your project knowledge base
- Chat commands: `/help`, `/status`, `/history`, `/clear`, `/sources`
- Conversation history and context
- Save chat sessions to `.sage/chats/`
- Type `exit` to quit

### `sage status`
Display the current status of your knowledge base.

### `sage version`
Show the installed version of Project Sage.

## Configuration

Sage stores its configuration in `.sage/config.json` within your project directory. This file contains:
- LLM provider settings
- API keys (stored securely)
- Document language preferences
- Chunking parameters

The `.sage/` directory is automatically added to your `.gitignore` to prevent accidentally committing sensitive information.

## Supported File Types

- **PDF** - Including scanned/image-based PDFs (via OCR)
- **DOCX** - Microsoft Word documents
- **PPTX** - PowerPoint presentations
- **XLSX** - Excel spreadsheets
- **TXT** - Plain text files
- **MD** - Markdown files

## API Keys

You'll need an API key from one of the supported providers:

- **Google Gemini**: Get your key at https://makersuite.google.com/app/apikey
- **Anthropic Claude**: Get your key at https://console.anthropic.com/
- **OpenAI GPT**: Get your key at https://platform.openai.com/api-keys

## Example Usage

```bash
# Initialize in a project folder
cd ~/projects/renewable-energy-project
sage setup

# Index all documents
sage update

# Ask questions in English (even about Vietnamese documents)
sage ask "What are the key milestones in the project timeline?"
sage ask "What is the total investment amount mentioned in the contracts?"
sage ask "List all the technical specifications for the solar panels"

# Check status
sage status

# Force re-index after adding new documents
sage update --force

# Launch the enhanced GUI
sage gui

# Start interactive chat session
sage chat
```

## Interactive Chat Example

```bash
$ sage chat
╭─────────────── Chat Session Started ───────────────╮
│ 🤖 Sage Interactive Chat                           │
│                                                     │
│ Project: renewable-energy-project                   │
│ Documents: 24 chunks indexed                        │
│ LLM: Google gemini-1.5-pro                         │
│                                                     │
│ Type your questions or 'exit' to quit              │
│ Commands: /help, /status, /clear, /history          │
╰─────────────────────────────────────────────────────╯

🧑 You: What is the total project budget?

╭─────────────────── 🤖 Sage ───────────────────────╮
│ The total project budget is $45 million USD as    │
│ stated in the project overview document.          │
╰────────────────────────────────────────────────────╯
📚 project_overview.md, financial_summary.xlsx

🧑 You: How is this budget allocated?

╭─────────────────── 🤖 Sage ───────────────────────╮
│ The budget is allocated as follows:               │
│ • Equipment: $28M (62%)                           │
│ • Construction: $12M (27%)                        │
│ • Development: $3M (7%)                           │
│ • Contingency: $2M (4%)                          │
╰────────────────────────────────────────────────────╯
📚 budget_breakdown.pdf, cost_analysis.xlsx

🧑 You: /history

Conversation History (2 questions):

1. Q: What is the total project budget?...
   A: The total project budget is $45 million USD...

2. Q: How is this budget allocated?...
   A: The budget is allocated as follows: • Equipment: $28M...

🧑 You: exit

Chat session ended. Asked 2 questions.
Save conversation history? [y/N]: y
Conversation saved to: .sage/chats/chat_20250810_142315.json
```

## Enhanced GUI Features

The `sage gui` command launches a comprehensive interface with multiple tabs:

### Overview Tab
- Real-time project statistics
- File count and chunk count
- Last update timestamp
- Quick action buttons for indexing

### Files Tab
- Complete list of all indexed documents
- **Double-click files to open them** in default application
- **Right-click context menu** with options:
  - Open file
  - Show in Finder/Explorer
  - Copy file path
  - Reindex single file
- Search and filter capabilities
- File details including chunk count and modification dates
- File type indicators and status

### Vectors Tab
- Vector database statistics
- Sample document chunks with content previews
- Vector embedding information
- Database storage details

### Query Tab
- Interactive question interface
- Real-time answer generation
- Source document references
- Response history

### Config Tab
- Current configuration display
- LLM provider and model settings
- Chunk size and overlap parameters

## Troubleshooting

### OCR Not Working
- Ensure Tesseract is installed: `tesseract --version`
- Install language packs for your documents (e.g., `tesseract-ocr-vie` for Vietnamese)

### API Errors
- Verify your API key is correct
- Check your internet connection
- Ensure you have sufficient API credits/quota

### Memory Issues
- For large projects, consider adjusting chunk_size in the configuration
- Process documents in batches if needed

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.