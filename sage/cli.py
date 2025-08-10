"""Command-line interface for Project Sage."""

import sys
import json
from pathlib import Path
from typing import Optional
import typer
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

from sage.config import ConfigManager, SageConfig
from sage.setup_gui import SetupWindow
from sage.file_processor import FileProcessor
from sage.vector_store import VectorStore
from sage.llm_client import LLMClient

app = typer.Typer(
    name="sage",
    help="Project Sage - An intelligent AI assistant for complex project management",
    add_completion=False
)
console = Console()


@app.command()
def setup():
    """Launch GUI to initialize Sage for this project."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    if config_manager.exists():
        if not typer.confirm("Configuration already exists. Do you want to reconfigure?"):
            return
            
    console.print("[bold blue]Launching setup window...[/bold blue]")
    
    try:
        setup_window = SetupWindow(project_path)
        config = setup_window.run()
        
        if config:
            console.print("[bold green]✓ Project initialized successfully![/bold green]")
            console.print(f"Configuration saved to: {config_manager.config_path}")
        else:
            console.print("[yellow]Setup cancelled.[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Error during setup: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def update(force: bool = typer.Option(False, "--force", "-f", help="Force full re-scan of all files")):
    """Scan and index project documents."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    console.print("[bold blue]Updating knowledge base...[/bold blue]")
    
    # Initialize components
    processor = FileProcessor(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        ocr_language=config.document_language
    )
    vector_store = VectorStore(config)
    vector_store.initialize()
    
    # Find files to process
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning for files...", total=None)
        files_to_process = processor.find_files(project_path, force)
        progress.update(task, completed=100)
        
    if not files_to_process:
        console.print("[green]✓ Knowledge base is up to date.[/green]")
        return
        
    console.print(f"Found [bold]{len(files_to_process)}[/bold] files to process")
    
    # Clear vector store if force update
    if force:
        vector_store.clear()
        
    # Process files
    total_documents = 0
    failed_files = []
    
    with Progress() as progress:
        task = progress.add_task("Processing files...", total=len(files_to_process))
        
        for file_path in files_to_process:
            progress.update(task, description=f"Processing {file_path.name}...")
            
            try:
                documents = processor.process_file(file_path)
                if documents:
                    vector_store.add_documents(documents)
                    processor.update_metadata(project_path, file_path, documents)
                    total_documents += len(documents)
                else:
                    failed_files.append(file_path)
                    
            except Exception as e:
                console.print(f"[red]Error processing {file_path.name}: {str(e)}[/red]")
                failed_files.append(file_path)
                
            progress.update(task, advance=1)
            
    # Print summary
    console.print("\n[bold]Update Summary:[/bold]")
    console.print(f"  Files processed: {len(files_to_process) - len(failed_files)}")
    console.print(f"  Documents created: {total_documents}")
    if failed_files:
        console.print(f"  [red]Failed files: {len(failed_files)}[/red]")
        for f in failed_files[:5]:
            console.print(f"    - {f.name}")
        if len(failed_files) > 5:
            console.print(f"    ... and {len(failed_files) - 5} more")
            
    console.print("[bold green]✓ Knowledge base updated successfully![/bold green]")


@app.command()
def ask(query: str = typer.Argument(..., help="Your question about the project")):
    """Ask a question about your project documents."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    # Initialize components
    vector_store = VectorStore(config)
    vector_store.initialize()
    
    # Check if knowledge base exists
    doc_count = vector_store.get_document_count()
    if doc_count == 0:
        console.print("[bold yellow]Knowledge base is empty. Run 'sage update' first.[/bold yellow]")
        raise typer.Exit(1)
        
    # Search for relevant documents
    with console.status("[bold blue]Searching knowledge base...[/bold blue]"):
        documents = vector_store.search(query, k=5)
        
    if not documents:
        console.print("[yellow]No relevant documents found for your query.[/yellow]")
        return
        
    # Get answer from LLM
    with console.status("[bold blue]Generating answer...[/bold blue]"):
        llm_client = LLMClient(config)
        result = llm_client.answer_question(query, documents)
        
    # Display answer
    answer_panel = Panel(
        result['answer'],
        title="[bold]Answer[/bold]",
        border_style="blue"
    )
    console.print(answer_panel)
    
    # Display sources
    if result['sources']:
        console.print("\n[bold]Sources:[/bold]")
        for source in result['sources']:
            # Make path relative to project
            try:
                rel_path = Path(source).relative_to(project_path)
                console.print(f"  • {rel_path}")
            except:
                console.print(f"  • {source}")
                
    if result.get('error'):
        console.print("\n[bold red]Note: There was an error generating the answer. Please check your API key and connection.[/bold red]")


@app.command()
def status():
    """Show the status of the Sage knowledge base."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    # Get vector store info
    vector_store = VectorStore(config)
    vector_store.initialize()
    doc_count = vector_store.get_document_count()
    
    # Get file metadata
    processor = FileProcessor()
    metadata = processor.load_metadata(project_path)
    
    # Create status table
    table = Table(title="Project Sage Status", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Project Path", str(project_path))
    table.add_row("LLM Provider", config.llm_provider.title())
    table.add_row("LLM Model", config.llm_model)
    table.add_row("Document Language", config.document_language.upper())
    table.add_row("Files Indexed", str(len(metadata)))
    table.add_row("Total Chunks", str(doc_count))
    
    # Find last update time
    if metadata:
        last_update = max(
            datetime.fromisoformat(m['processed_at']) 
            for m in metadata.values()
        )
        table.add_row("Last Update", last_update.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        table.add_row("Last Update", "Never")
        
    console.print(table)
    
    if doc_count == 0:
        console.print("\n[yellow]Knowledge base is empty. Run 'sage update' to index your documents.[/yellow]")


@app.command()
def gui():
    """Launch the enhanced GUI application."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    console.print("[bold blue]Launching Sage GUI...[/bold blue]")
    
    try:
        from sage.gui_app import SageGUI
        app = SageGUI(project_path)
        app.run()
    except ImportError as e:
        console.print(f"[bold red]Error: Missing GUI dependencies: {str(e)}[/bold red]")
        console.print("Install GUI dependencies with: pip install matplotlib")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error launching GUI: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def chat():
    """Start an interactive chat session with your project documents."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    # Initialize components
    vector_store = VectorStore(config)
    vector_store.initialize()
    
    # Check if knowledge base exists
    doc_count = vector_store.get_document_count()
    if doc_count == 0:
        console.print("[bold yellow]Knowledge base is empty. Run 'sage update' first.[/bold yellow]")
        raise typer.Exit(1)
        
    llm_client = LLMClient(config)
    
    # Start chat session
    console.print(Panel.fit(
        f"[bold blue]🤖 Sage Interactive Chat[/bold blue]\n\n"
        f"Project: {project_path.name}\n"
        f"Documents: {doc_count} chunks indexed\n"
        f"LLM: {config.llm_provider.title()} {config.llm_model}\n\n"
        f"[dim]Type your questions or 'exit' to quit\n"
        f"Commands: /help, /status, /clear, /history[/dim]",
        title="Chat Session Started",
        border_style="blue"
    ))
    
    conversation_history = []
    
    try:
        while True:
            # Get user input
            try:
                question = typer.prompt("\n🧑 You", prompt_suffix="")
            except (KeyboardInterrupt, EOFError):
                break
                
            # Handle special commands
            if question.lower().strip() in ['exit', 'quit', 'bye']:
                break
            elif question.strip().startswith('/'):
                _handle_chat_command(question.strip(), conversation_history, vector_store, config)
                continue
            elif not question.strip():
                continue
                
            # Process the question
            with console.status("[bold blue]🤖 Sage is thinking...[/bold blue]"):
                try:
                    # Search for relevant documents
                    documents = vector_store.search(question, k=5)
                    
                    if not documents:
                        console.print("[yellow]No relevant documents found for your question.[/yellow]")
                        continue
                        
                    # Get answer from LLM
                    result = llm_client.answer_question(question, documents)
                    
                    if result.get('error'):
                        console.print(f"[bold red]Error: {result['answer']}[/bold red]")
                        continue
                        
                    # Display answer
                    answer_panel = Panel(
                        result['answer'],
                        title="[bold]🤖 Sage[/bold]",
                        border_style="green"
                    )
                    console.print(answer_panel)
                    
                    # Display sources (compact format)
                    if result['sources']:
                        sources_text = "📚 " + ", ".join([
                            Path(source).relative_to(project_path).name 
                            for source in result['sources']
                        ])
                        console.print(f"[dim]{sources_text}[/dim]")
                        
                    # Add to conversation history
                    conversation_history.append({
                        'question': question,
                        'answer': result['answer'],
                        'sources': result['sources'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    console.print(f"[bold red]Error: {str(e)}[/bold red]")
                    console.print("[dim]Check your API key and internet connection[/dim]")
                    
    except KeyboardInterrupt:
        pass
        
    # End chat session
    console.print(f"\n[bold blue]Chat session ended. Asked {len(conversation_history)} questions.[/bold blue]")
    if conversation_history:
        save_chat = typer.confirm("Save conversation history?")
        if save_chat:
            _save_chat_history(project_path, conversation_history)


def _handle_chat_command(command: str, history: list, vector_store: VectorStore, config: SageConfig):
    """Handle special chat commands."""
    cmd = command.lower().strip()
    
    if cmd == '/help':
        help_text = """[bold]Available Commands:[/bold]
        
🔹 /help     - Show this help message
🔹 /status   - Show knowledge base status  
🔹 /clear    - Clear conversation history
🔹 /history  - Show conversation history
🔹 /sources  - List all indexed documents
🔹 exit      - End chat session

[bold]Tips:[/bold]
• Ask specific questions about your project documents
• Reference file names or document types in your questions
• Use follow-up questions to dive deeper into topics"""
        
        console.print(Panel(help_text, title="Chat Help", border_style="yellow"))
        
    elif cmd == '/status':
        doc_count = vector_store.get_document_count()
        status_text = f"""[bold]Knowledge Base Status:[/bold]

📊 Documents: {doc_count} chunks indexed
🤖 LLM: {config.llm_provider.title()} {config.llm_model}  
📝 Language: {config.document_language.upper()}
💬 Questions Asked: {len(history)}"""
        
        console.print(Panel(status_text, title="Status", border_style="cyan"))
        
    elif cmd == '/clear':
        history.clear()
        console.print("[yellow]Conversation history cleared.[/yellow]")
        
    elif cmd == '/history':
        if not history:
            console.print("[yellow]No conversation history yet.[/yellow]")
            return
            
        console.print(f"[bold]Conversation History ({len(history)} questions):[/bold]\n")
        for i, item in enumerate(history[-5:], 1):  # Show last 5
            console.print(f"[cyan]{i}. Q:[/cyan] {item['question'][:100]}...")
            console.print(f"[green]   A:[/green] {item['answer'][:150]}...\n")
            
    elif cmd == '/sources':
        # Get unique sources from conversation
        all_sources = set()
        for item in history:
            all_sources.update(item.get('sources', []))
            
        if all_sources:
            console.print("[bold]Documents referenced in conversation:[/bold]")
            for source in sorted(all_sources):
                try:
                    rel_path = Path(source).relative_to(Path.cwd())
                    console.print(f"📄 {rel_path}")
                except:
                    console.print(f"📄 {source}")
        else:
            console.print("[yellow]No sources referenced yet.[/yellow]")
            
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("[dim]Type '/help' for available commands[/dim]")


def _save_chat_history(project_path: Path, history: list):
    """Save conversation history to file."""
    try:
        chat_dir = project_path / ".sage" / "chats"
        chat_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_{timestamp}.json"
        
        chat_file = chat_dir / filename
        with open(chat_file, 'w') as f:
            json.dump({
                'project_path': str(project_path),
                'timestamp': datetime.now().isoformat(),
                'question_count': len(history),
                'conversation': history
            }, f, indent=2)
            
        console.print(f"[green]Conversation saved to: {chat_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to save conversation: {e}[/red]")


@app.command()
def version():
    """Show Sage version."""
    from sage import __version__
    console.print(f"Project Sage v{__version__}")


def main():
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()